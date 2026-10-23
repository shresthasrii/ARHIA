import re
import datetime
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.database import SessionLocal, init_db
from backend.models import KnowledgeConcept

logger = logging.getLogger("ARHIEA.KnowledgeEngine")

class KnowledgeBaseEngine:
    def __init__(self):
        self._ensure_initialized = False

    def _init_if_needed(self):
        if not self._ensure_initialized:
            try:
                init_db()
                self._ensure_initialized = True
            except Exception as e:
                logger.warning(f"Database init notice: {e}")

    def teach_concept(
        self,
        topic: str,
        content: str,
        category: str = "General Knowledge",
        summary: Optional[str] = None,
        keywords: Optional[str] = None,
        source: str = "user_taught",
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Adds or updates a learned concept in the AI knowledge base."""
        self._init_if_needed()
        clean_topic = topic.strip()
        clean_content = content.strip()
        if not clean_topic or not clean_content:
            return {"status": "error", "message": "Topic and content are required."}

        # Auto-generate summary if missing
        if not summary or not summary.strip():
            first_sentence = clean_content.split(".")[0].strip()
            summary = first_sentence[:250] + ("." if not first_sentence.endswith(".") else "")

        # Auto-generate keywords if missing
        if not keywords:
            words = set(re.findall(r"\b[a-zA-Z0-9_\-\.]{3,}\b", f"{clean_topic} {summary}".lower()))
            common_stopwords = {"the", "and", "for", "with", "that", "this", "from", "are", "was", "were", "what", "which", "how"}
            keywords = ", ".join([w for w in words if w not in common_stopwords][:12])

        db = SessionLocal()
        try:
            concept = db.query(KnowledgeConcept).filter(KnowledgeConcept.topic.ilike(clean_topic)).first()
            if concept:
                concept.content = clean_content
                concept.summary = summary
                concept.category = category
                concept.keywords = keywords
                concept.source = source
                concept.confidence = confidence
                concept.updated_at = datetime.datetime.utcnow()
                db.commit()
                db.refresh(concept)
                action = "updated"
            else:
                concept = KnowledgeConcept(
                    topic=clean_topic,
                    category=category,
                    summary=summary,
                    content=clean_content,
                    keywords=keywords,
                    source=source,
                    confidence=confidence,
                    created_at=datetime.datetime.utcnow()
                )
                db.add(concept)
                db.commit()
                db.refresh(concept)
                action = "created"

            return {
                "status": "success",
                "action": action,
                "id": concept.id,
                "topic": concept.topic,
                "category": concept.category,
                "summary": concept.summary,
                "source": concept.source
            }
        except Exception as e:
            logger.error(f"Error teaching concept '{clean_topic}': {e}")
            return {"status": "error", "message": str(e)}
        finally:
            db.close()

    def search_knowledge(self, query: str, limit: int = 3, threshold: float = 0.25) -> List[Dict[str, Any]]:
        """
        Fast, token-weighted semantic search across topics, keywords, and summaries.
        Returns matching concepts sorted by relevance score.
        """
        self._init_if_needed()
        q_clean = query.strip().lower()
        if not q_clean:
            return []

        # Strip common question prefix
        q_core = re.sub(
            r"^(what('s| is| are| was| were)?|who('s| is| was)?|explain|tell me about|how does|how do|describe)\s+",
            "",
            q_clean
        ).strip().rstrip("?.!")

        query_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", q_core))
        if not query_tokens:
            query_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", q_clean))

        db = SessionLocal()
        try:
            candidates = db.query(KnowledgeConcept).all()
            scored: List[Tuple[float, KnowledgeConcept]] = []

            for c in candidates:
                topic_low = c.topic.lower()
                summary_low = c.summary.lower()
                kw_low = (c.keywords or "").lower()

                score = 0.0

                # 1. Exact or near-exact match on topic
                if q_core == topic_low:
                    score += 10.0
                elif topic_low in q_core or q_core in topic_low:
                    score += 5.0

                # 2. Token overlap with topic
                topic_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", topic_low))
                overlap_topic = query_tokens.intersection(topic_tokens)
                if topic_tokens:
                    score += (len(overlap_topic) / len(topic_tokens)) * 4.0

                # 3. Token overlap with keywords
                kw_tokens = set(re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", kw_low))
                overlap_kw = query_tokens.intersection(kw_tokens)
                if overlap_kw:
                    score += min(len(overlap_kw) * 1.5, 3.0)

                # 4. Phrase containment in summary or content
                if q_core in summary_low:
                    score += 2.0

                if score >= threshold:
                    scored.append((score, c))

            scored.sort(key=lambda x: x[0], reverse=True)

            results = []
            for score, c in scored[:limit]:
                results.append({
                    "id": c.id,
                    "topic": c.topic,
                    "category": c.category,
                    "summary": c.summary,
                    "content": c.content,
                    "keywords": c.keywords,
                    "source": c.source,
                    "confidence": c.confidence,
                    "relevance_score": round(score, 2)
                })
            return results
        except Exception as e:
            logger.error(f"Search knowledge error: {e}")
            return []
        finally:
            db.close()

    def format_concept_response(self, concept: Dict[str, Any]) -> str:
        """Formats a learned concept into an articulate, structured AI response."""
        topic = concept["topic"]
        category = concept.get("category", "Knowledge")
        summary = concept.get("summary", "")
        content = concept.get("content", "")
        source = concept.get("source", "curated_pretrain")

        source_badge = "Neural Core Knowledge" if source == "curated_pretrain" else "User Taught & Learned" if source == "user_taught" else "Ingested Knowledge"

        resp_lines = [
            f"### **{topic}**",
            f"*Domain: {category} | Status: {source_badge}*",
            "",
            f"**Executive Definition**:\n{summary}",
            "",
            "**Detailed Analysis & Insights**:",
            content,
            "",
            "---",
            f"> [!NOTE]\n> Retrieved from ARHIEA's internal learned knowledge base. You can ask follow-ups or teach me new facts on this topic."
        ]
        return "\n".join(resp_lines)

    def train_from_text(self, raw_text: str, category: str = "Document Trained", source: str = "document_trained") -> Dict[str, Any]:
        """
        Parses multi-paragraph or key-value training text, extracts distinct concepts,
        and ingests them into the persistent neural brain.
        """
        self._init_if_needed()
        text = raw_text.strip()
        if not text:
            return {"status": "error", "message": "Text is empty."}

        learned = []
        # Pattern A: Look for Topic / Definition pairs ("Topic: ... Definition: ...") or ("## Topic ...")
        # Split by double newlines or markdown headers
        sections = re.split(r"\n{2,}|(?=^#{1,3}\s+)", text, flags=re.MULTILINE)

        for sec in sections:
            sec = sec.strip()
            if not sec or len(sec) < 15:
                continue

            # Check if header format: "# Topic\nContent..."
            header_match = re.match(r"^#{1,3}\s+(.+?)\n+(.+)$", sec, re.DOTALL)
            colon_match = re.match(r"^([^:\n]{3,60}):\s+(.+)$", sec, re.DOTALL)

            topic = None
            content = None

            if header_match:
                topic = header_match.group(1).strip()
                content = header_match.group(2).strip()
            elif colon_match and not colon_match.group(1).lower().startswith(("http", "note", "tip", "warning")):
                topic = colon_match.group(1).strip()
                content = colon_match.group(2).strip()
            else:
                # Use first sentence as topic if short, or summarize
                first_line = sec.split("\n")[0].strip()
                if len(first_line) <= 60 and ("." not in first_line or first_line.endswith(".")):
                    topic = first_line.rstrip(".")
                    content = sec[len(first_line):].strip() or sec
                else:
                    topic = first_line[:50].strip()
                    content = sec

            if topic and content:
                res = self.teach_concept(
                    topic=topic,
                    content=content,
                    category=category,
                    source=source
                )
                if res.get("status") == "success":
                    learned.append(topic)

        # Fallback if no sections detected: ingest entire block as a single concept
        if not learned:
            first_line = text.split("\n")[0][:50].strip()
            topic = first_line or "Ingested Document"
            res = self.teach_concept(topic=topic, content=text, category=category, source=source)
            if res.get("status") == "success":
                learned.append(topic)

        return {
            "status": "success",
            "concepts_learned": len(learned),
            "topics": learned,
            "category": category
        }

    def detect_and_learn_from_chat(self, user_text: str) -> Optional[Dict[str, Any]]:
        """
        Detects if the user is naturally teaching the AI something in conversation:
        - "remember that <X> is <Y>"
        - "learn that <X> is <Y>"
        - "teach you: <X> means <Y>"
        - "teach arhiea that <X> is <Y>"
        """
        t = user_text.strip()
        t_low = t.lower()

        patterns = [
            r"^(?:please\s+)?(?:remember\s+that|learn\s+that|teach\s+you\s+that|teach\s+arhiea\s+that)\s+([^:=]+?)\s+(?:is|means|equals|represents)\s+(.+)$",
            r"^(?:teach|learn)\s*:\s*([^:=]+?)\s*(?:=|:|-|>|means|is)\s*(.+)$",
            r"^(?:teach\s+arhiea|teach\s+me)\s+(?:about\s+)?([^:]+?)\s*:\s*(.+)$",
            r"^(?:note\s+that|keep\s+in\s+mind\s+that)\s+([^:=]+?)\s+(?:is|means|equals)\s+(.+)$"
        ]

        for pat in patterns:
            m = re.match(pat, t, re.IGNORECASE)
            if m:
                topic = m.group(1).strip()
                content = m.group(2).strip()
                if len(topic) >= 2 and len(content) >= 3:
                    res = self.teach_concept(
                        topic=topic,
                        content=content,
                        category="User Learned",
                        source="user_taught"
                    )
                    ack = (
                        f"🧠 **Knowledge Learned & Saved!**\n\n"
                        f"I have committed this to my persistent neural memory:\n"
                        f"- **Topic**: **{topic}**\n"
                        f"- **Fact**: {content}\n\n"
                        f"> [!TIP]\n> You can ask me about **{topic}** anytime, and I will recall it instantly!"
                    )
                    return {
                        "response": ack,
                        "tool": "teach_concept",
                        "topic": topic,
                        "verified": True
                    }

        return None

    def get_all_concepts(self, category: Optional[str] = None, limit: int = 150) -> List[Dict[str, Any]]:
        self._init_if_needed()
        db = SessionLocal()
        try:
            q = db.query(KnowledgeConcept)
            if category and category.lower() != "all":
                q = q.filter(KnowledgeConcept.category.ilike(category))
            concepts = q.order_by(KnowledgeConcept.updated_at.desc(), KnowledgeConcept.id.desc()).limit(limit).all()
            return [
                {
                    "id": c.id,
                    "topic": c.topic,
                    "category": c.category,
                    "summary": c.summary,
                    "content": c.content,
                    "keywords": c.keywords,
                    "source": c.source,
                    "confidence": c.confidence,
                    "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else None,
                    "updated_at": c.updated_at.strftime("%Y-%m-%d %H:%M") if c.updated_at else None
                }
                for c in concepts
            ]
        finally:
            db.close()

    def delete_concept(self, concept_id: int) -> bool:
        self._init_if_needed()
        db = SessionLocal()
        try:
            concept = db.query(KnowledgeConcept).filter(KnowledgeConcept.id == concept_id).first()
            if concept:
                db.delete(concept)
                db.commit()
                return True
            return False
        finally:
            db.close()

    def get_stats(self) -> Dict[str, Any]:
        self._init_if_needed()
        db = SessionLocal()
        try:
            all_concepts = db.query(KnowledgeConcept).all()
            total = len(all_concepts)
            categories: Dict[str, int] = {}
            sources: Dict[str, int] = {}

            for c in all_concepts:
                categories[c.category] = categories.get(c.category, 0) + 1
                sources[c.source] = sources.get(c.source, 0) + 1

            return {
                "total_concepts": total,
                "categories": categories,
                "sources": sources,
                "last_trained": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            }
        finally:
            db.close()

    def seed_default_knowledge(self, force: bool = False) -> int:
        """
        Seeds an extensive, multi-domain curriculum into the AI brain.
        Includes Emergency & Road Safety (SIH), Computer Science, Physics, Chemistry, Biology, Math, History.
        """
        self._init_if_needed()
        db = SessionLocal()
        try:
            existing_count = db.query(KnowledgeConcept).count()
            if existing_count > 20 and not force:
                logger.info(f"Knowledge base already initialized with {existing_count} concepts.")
                return existing_count
        finally:
            db.close()

        curriculum = [
            # -------------------------------------------------------------
            # SIH Emergency & Road Intelligence
            # -------------------------------------------------------------
            {
                "topic": "CPR (Cardiopulmonary Resuscitation)",
                "category": "Road & Emergency Intelligence",
                "summary": "Life-saving emergency procedure consisting of chest compressions and rescue breaths to maintain blood circulation to vital organs.",
                "content": (
                    "**Step-by-Step Emergency CPR Protocol**:\n"
                    "1. **Check Scene Safety & Responsiveness**: Tap shoulders firmly and shout 'Are you okay?'. Check for normal breathing for no more than 10 seconds.\n"
                    "2. **Call for Emergency Help**: Dial 112 (India/EU) or 911 (US). Request an AED (Automated External Defibrillator).\n"
                    "3. **Position Hands**: Place heel of one hand in center of patient's chest (lower half of sternum), interlock fingers of other hand.\n"
                    "4. **Compression Rate & Depth**: Compress at 100-120 beats per minute (rhythm of 'Stayin' Alive') to a depth of 5-6 cm (2-2.4 inches) for adults. Allow full chest recoil.\n"
                    "5. **Compression-to-Breath Ratio**: 30 high-quality compressions followed by 2 gentle rescue breaths (tilt head back, pinch nose, deliver 1-second breath). If untrained, perform continuous Hands-Only CPR."
                ),
                "keywords": "cpr, heart attack, cardiac arrest, chest compressions, emergency, first aid, aed, breathing"
            },
            {
                "topic": "Vehicle Brake Failure Protocol",
                "category": "Road & Emergency Intelligence",
                "summary": "Emergency recovery procedure when a vehicle's hydraulic brakes fail while moving.",
                "content": (
                    "**Immediate Action Protocol for Brake Failure**:\n"
                    "1. **Do NOT Panic or Turn Off Engine**: Turning off the ignition locks the steering column and removes power steering.\n"
                    "2. **Pump the Brake Pedal Rapidly**: Modern dual-split brake systems may regain hydraulic pressure after 3-4 firm pumps.\n"
                    "3. **Downshift Progressively (Engine Braking)**: Shift from 5th to 4th, then 3rd, 2nd, and 1st gear. In automatics, shift to 'L' or manual paddle downshifts.\n"
                    "4. **Gently Apply Handbrake**: Once speed is under 40 km/h, pull the emergency handbrake gradually while holding the release ratchet button to prevent rear wheels from locking and skidding.\n"
                    "5. **Use Friction / Soft Verge**: Steer towards gravel shoulders, sand traps, or gentle upward slopes. Flash hazard lights and honk horn to warn surrounding motorists."
                ),
                "keywords": "brake failure, brakes failed, car emergency, engine braking, handbrake, stopping vehicle"
            },
            {
                "topic": "Aquaplaning (Hydroplaning) Recovery",
                "category": "Road & Emergency Intelligence",
                "summary": "Hazardous condition where a layer of water builds up between tyres and the road surface, leading to loss of traction and steering control.",
                "content": (
                    "**How to Recover from Aquaplaning**:\n"
                    "1. **Do NOT Slam the Brakes**: Sudden braking locks the wheels and can induce uncontrollable spinning.\n"
                    "2. **Ease Off the Accelerator Gently**: Allow vehicle momentum to slow down naturally until tyre tread disperses water and reconnects with tarmac.\n"
                    "3. **Hold Steering Wheel Straight**: Maintain the direction of travel without jerky corrections. Steer into the skid only if the tail starts sliding.\n"
                    "4. **Prevention Guidelines**: Maintain tyre tread depth above 3mm, ensure correct PSI inflation, and reduce speed by at least 15-20 km/h during heavy rainfall."
                ),
                "keywords": "aquaplaning, hydroplaning, wet road, rain driving, skidding, traction loss, tyre tread"
            },
            {
                "topic": "Tyre Blowout Emergency Procedure",
                "category": "Road & Emergency Intelligence",
                "summary": "Critical procedure to regain control when a tyre bursts unexpectedly at highway speed.",
                "content": (
                    "**Procedure for Handling High-Speed Tyre Blowout**:\n"
                    "1. **Grip Steering Wheel with Both Hands**: Expect a violent pull towards the side of the blown tyre. Keep steering centered.\n"
                    "2. **Avoid Heavy Braking**: Sudden braking shifts vehicle weight forward, severely destabilizing the damaged axle.\n"
                    "3. **Tap Accelerator Briefly, Then Coast**: A brief tap can stabilize forward momentum, then lift foot and let aerodynamic drag and rolling resistance decelerate the car.\n"
                    "4. **Indicate & Pull Safely Off Highway**: Once vehicle speed drops below 30 km/h, gently brake, turn on hazard flashers, and pull completely onto the emergency shoulder."
                ),
                "keywords": "tyre blowout, tire burst, punctured tyre, highway emergency, car control"
            },
            {
                "topic": "First Aid for Severe Thermal Burns",
                "category": "Road & Emergency Intelligence",
                "summary": "Medical emergency guidelines for treating second- and third-degree heat burns.",
                "content": (
                    "**Burn Treatment Rules**:\n"
                    "1. **Cool with Running Tap Water for 20 Minutes**: Use cool (not freezing or iced) water immediately. Ice causes tissue vasoconstriction and worsens ischemia.\n"
                    "2. **Remove Constrictive Items**: Remove rings, watches, tight clothing before edema (swelling) sets in.\n"
                    "3. **Never Pop Blisters or Apply Butter/Oils**: Popping blisters introduces pathogens. Oils trap heat inside the dermis.\n"
                    "4. **Cover Loosely with Clean Cling Film or Sterile Dressing**: Protects nerve endings from exposure to air and minimizes infection.\n"
                    "5. **Seek Emergency Medical Help**: Required for burns covering >10% of body, facial/joint burns, chemical/electrical burns, or white/charred painless burns (3rd degree)."
                ),
                "keywords": "burns, first aid, thermal burn, blister, scalding, emergency medical"
            },
            {
                "topic": "Heimlich Maneuver (Choking Relief)",
                "category": "Road & Emergency Intelligence",
                "summary": "Emergency first aid procedure used to clear a foreign object obstructing a person's airway.",
                "content": (
                    "**Heimlich Maneuver Steps for Conscious Adults**:\n"
                    "1. **Verify Complete Choking**: Ask 'Are you choking?'. If the victim cannot speak, cough, or breathe, initiate immediately.\n"
                    "2. **Position Behind Victim**: Stand behind them, place one foot forward between their legs for balance.\n"
                    "3. **Make a Fist**: Place thumb side of fist slightly above the navel and well below the xiphoid process (breastbone).\n"
                    "4. **Inward and Upward Thrusts**: Grasp your fist with your other hand and deliver quick, forceful upward and inward thrusts.\n"
                    "5. **Repeat Until Dislodged or Patient Becomes Unconscious**: If patient becomes unresponsive, lower carefully to the floor and begin CPR immediately."
                ),
                "keywords": "heimlich maneuver, choking, airway obstruction, abdominal thrusts, first aid"
            },
            {
                "topic": "Golden Hour in Trauma & Accident Management",
                "category": "Road & Emergency Intelligence",
                "summary": "The critical first 60 minutes following severe physical trauma where prompt definitive medical intervention dramatically increases survival rates.",
                "content": (
                    "**Golden Hour Principles**:\n"
                    "- **Rapid Scene Triage**: Ensure personal safety, assess responsiveness, airway, breathing, circulation (ABCDE protocol).\n"
                    "- **C-Spine Stabilization**: In vehicular crashes, always suspect spinal injury. Do not twist or bend neck/back unless immediate fire/submersion risk exists.\n"
                    "- **Hemorrhage Control**: Apply firm, direct pressure with clean cloth or tourniquet 2-3 inches proximal to severe arterial bleeding on limbs.\n"
                    "- **Emergency SOS Dispatch**: Convey exact GPS coordinates, number of injured, and presence of pinned passengers to emergency services (112 / 108 / 911)."
                ),
                "keywords": "golden hour, trauma, road accident, triage, c-spine, bleeding control, emergency"
            },

            # -------------------------------------------------------------
            # Computer Science & Software Engineering
            # -------------------------------------------------------------
            {
                "topic": "Transformer Architecture & Self-Attention",
                "category": "Computer Science & AI",
                "summary": "The foundational deep learning architecture behind modern Large Language Models (LLMs) such as GPT-4, Gemini, Claude, and DeepSeek.",
                "content": (
                    "**Core Transformer Mechanisms**:\n"
                    "- **Attention Is All You Need (Vaswani et al., 2017)**: Replaced recurrent architectures (RNN/LSTM) with parallelized self-attention.\n"
                    "- **Scaled Dot-Product Attention Formula**:\n"
                    "  $$\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V$$\n"
                    "- **Multi-Head Attention**: Allows the model to jointly attend to information from different representation subspaces at different positions.\n"
                    "- **Positional Encoding**: Injects sequence order information since self-attention operations are permutation-equivariant.\n"
                    "- **Feed-Forward Networks & LayerNorm**: Processes attended representations with non-linear activations (GELU/SwiGLU) and residual connections."
                ),
                "keywords": "transformer, self-attention, llm, neural network, gpt, deep learning, qkv, deepseek"
            },
            {
                "topic": "Binary Search Algorithm",
                "category": "Computer Science & AI",
                "summary": "Highly efficient search algorithm that finds the position of a target value within a sorted array in logarithmic O(log n) time.",
                "content": (
                    "**Complexity & Implementation**:\n"
                    "- **Time Complexity**: $O(1)$ Best Case | $O(\\log n)$ Average & Worst Case.\n"
                    "- **Space Complexity**: $O(1)$ Iterative | $O(\\log n)$ Recursive call stack.\n\n"
                    "```python\n"
                    "def binary_search(arr: list[int], target: int) -> int:\n"
                    "    left, right = 0, len(arr) - 1\n"
                    "    while left <= right:\n"
                    "        mid = left + (right - left) // 2\n"
                    "        if arr[mid] == target:\n"
                    "            return mid\n"
                    "        elif arr[mid] < target:\n"
                    "            left = mid + 1\n"
                    "        else:\n"
                    "            right = mid - 1\n"
                    "    return -1\n"
                    "```"
                ),
                "keywords": "binary search, search algorithm, o(log n), algorithms, data structures, sorted array"
            },
            {
                "topic": "Dynamic Programming Principles",
                "category": "Computer Science & AI",
                "summary": "Algorithmic technique for solving complex optimization problems by breaking them down into simpler overlapping subproblems with optimal substructure.",
                "content": (
                    "**Two Key Hallmarks of DP**:\n"
                    "1. **Optimal Substructure**: An optimal solution to the problem contains optimal solutions to subproblems.\n"
                    "2. **Overlapping Subproblems**: The same subproblems are solved repeatedly rather than generating new ones.\n\n"
                    "**Approaches**:\n"
                    "- **Top-Down (Memoization)**: Recursion with caching (e.g. `@functools.lru_cache`).\n"
                    "- **Bottom-Up (Tabulation)**: Iterative filling of a DP table, often saving space through rolling variables (e.g. 0/1 Knapsack, Longest Common Subsequence, Edit Distance)."
                ),
                "keywords": "dynamic programming, memoization, tabulation, knapsack, algorithms, optimization"
            },
            {
                "topic": "RESTful API Architecture & Principles",
                "category": "Computer Science & AI",
                "summary": "Representational State Transfer architectural style for designing networked applications over HTTP.",
                "content": (
                    "**Core Constraints of REST**:\n"
                    "1. **Stateless**: Each request from client to server must contain all necessary context; server stores no session state.\n"
                    "2. **Client-Server Separation**: Separation of concerns between UI/client and storage/business logic.\n"
                    "3. **Uniform Interface**: Resource identification via URIs, manipulation through representations, self-descriptive messages, and HATEOAS.\n"
                    "4. **Cacheability**: Responses explicitly labeled as cacheable or non-cacheable.\n"
                    "5. **Standard HTTP Methods**: `GET` (safe/idempotent read), `POST` (create), `PUT` (idempotent replace), `PATCH` (partial update), `DELETE` (idempotent removal)."
                ),
                "keywords": "rest api, restful, http methods, crud, web architecture, json, stateless"
            },
            {
                "topic": "WebSockets Bidirectional Protocol",
                "category": "Computer Science & AI",
                "summary": "Full-duplex, persistent communication channel over a single TCP connection, ideal for real-time dashboards, chat, and telemetry.",
                "content": (
                    "**How WebSockets Work**:\n"
                    "- **Handshake**: Initiates as an HTTP request with `Upgrade: websocket` and `Connection: Upgrade` headers.\n"
                    "- **Switching Protocols (HTTP 101)**: The server agrees and upgrades the TCP socket to bidirectional framing.\n"
                    "- **Zero Polling Overhead**: Eliminates repeated HTTP header transmission (typical 1-2 KB per request reduced to 2-14 byte frames).\n"
                    "- **Use Cases**: Real-time gaming, financial market tickers, live chat, voice streaming, and ARHIEA's assistant telemetry engine."
                ),
                "keywords": "websockets, full duplex, real time, networking, tcp, http upgrade"
            },

            # -------------------------------------------------------------
            # Physics, Chemistry & Natural Sciences
            # -------------------------------------------------------------
            {
                "topic": "Einstein's Theory of Special and General Relativity",
                "category": "Physics & Cosmology",
                "summary": "Albert Einstein's revolutionary framework describing the interplay of spacetime, mass, energy, and gravitation.",
                "content": (
                    "**Special Relativity (1905)**:\n"
                    "- **Postulates**: Physics laws are invariant in all inertial reference frames; speed of light in vacuum ($c \\approx 3 \\times 10^8\\text{ m/s}$) is constant for all observers.\n"
                    "- **Consequences**: Time dilation (moving clocks tick slower), length contraction, and mass-energy equivalence: $E = mc^2$.\n\n"
                    "**General Relativity (1915)**:\n"
                    "- **Principle**: Gravity is not an attractive Newtonian force across a void, but the geometric curvature of 4D spacetime caused by mass and energy: $G_{\\mu\\nu} = \\frac{8\\pi G}{c^4} T_{\\mu\\nu}$.\n"
                    "- **Empirical Verifications**: Gravitational lensing, precession of Mercury's perihelion, gravitational time dilation (crucial for GPS satellite clock syncing), and gravitational waves (LIGO)."
                ),
                "keywords": "relativity, einstein, spacetime, e=mc2, gravity, time dilation, black holes, physics"
            },
            {
                "topic": "Quantum Mechanics & Wave-Particle Duality",
                "category": "Physics & Cosmology",
                "summary": "Fundamental theory in physics describing nature at the atomic and subatomic scale.",
                "content": (
                    "**Foundational Principles**:\n"
                    "- **Wave-Particle Duality (de Broglie)**: Matter exhibits both particulate and wavelike behaviors with wavelength $\\lambda = \\frac{h}{p}$.\n"
                    "- **Heisenberg Uncertainty Principle**: Position and momentum cannot be simultaneously measured with arbitrary precision: $\\Delta x \\cdot \\Delta p \\geq \\frac{\\hbar}{2}$.\n"
                    "- **Schrödinger Equation**: Describes quantum state evolution over time: $i\\hbar \\frac{\\partial}{\\partial t} \\Psi = \\hat{H} \\Psi$.\n"
                    "- **Quantum Superposition & Entanglement**: Quantum systems remain in a linear combination of states until observed; entangled pairs exhibit correlated properties regardless of spatial separation."
                ),
                "keywords": "quantum mechanics, schrodinger, wave particle, heisenberg, superposition, physics"
            },
            {
                "topic": "Photosynthesis & Cellular Energy Transfer",
                "category": "Biology & Medicine",
                "summary": "The biological process by which photosynthetic organisms convert light energy into chemical energy stored in glucose.",
                "content": (
                    "**Overall Chemical Equation**:\n"
                    "$$6\\text{CO}_2 + 6\\text{H}_2\\text{O} + \\text{photons} \\longrightarrow \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2$$\n\n"
                    "**Two Main Stages**:\n"
                    "1. **Light-Dependent Reactions (Thylakoid Membrane)**: Chlorophyll absorbs photons, splits $\\text{H}_2\\text{O}$ releasing $\\text{O}_2$, and generates ATP and NADPH via electron transport chains.\n"
                    "2. **Light-Independent Reactions / Calvin Cycle (Stroma)**: Enzyme RuBisCO fixes carbon dioxide (carbon fixation), utilizing ATP and NADPH to synthesize glyceraldehyde-3-phosphate (G3P), precursors to glucose."
                ),
                "keywords": "photosynthesis, chloroplasts, calvin cycle, atp, biology, plants, glucose, chlorophyll"
            },
            {
                "topic": "DNA Structure & The Genetic Code",
                "category": "Biology & Medicine",
                "summary": "Deoxyribonucleic acid is the hereditary molecule carrying the biological instructions for life and cellular synthesis.",
                "content": (
                    "**Molecular Architecture**:\n"
                    "- **Double Helix**: Discovered by James Watson, Francis Crick, Rosalind Franklin (1953). Consists of antiparallel sugar-phosphate backbones.\n"
                    "- **Complementary Base Pairing**: Adenine (A) pairs with Thymine (T) via 2 hydrogen bonds; Cytosine (C) pairs with Guanine (G) via 3 hydrogen bonds.\n"
                    "- **Central Dogma of Molecular Biology**:\n"
                    "  $$\\text{DNA} \\xrightarrow{\\text{Transcription}} \\text{mRNA} \\xrightarrow{\\text{Translation}} \\text{Protein}$$\n"
                    "- **Triplets (Codons)**: Sequences of 3 nucleotides encode one of 20 standard amino acids or stop signals."
                ),
                "keywords": "dna, rna, genetics, double helix, genes, proteins, transcription, translation, biology"
            },

            # -------------------------------------------------------------
            # Mathematics & Quantitative Reasoning
            # -------------------------------------------------------------
            {
                "topic": "Differential & Integral Calculus Fundamentals",
                "category": "Mathematics",
                "summary": "Mathematical study of continuous change, encompassing derivatives (rates of change) and integrals (accumulation).",
                "content": (
                    "**Derivatives (Instantaneous Rate of Change)**:\n"
                    "$$f'(x) = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$\n"
                    "- **Rules**: Power Rule: $\\frac{d}{dx}[x^n] = n x^{n-1}$, Product Rule: $(uv)' = u'v + uv'$, Chain Rule: $\\frac{d}{dx}[f(g(x))] = f'(g(x))g'(x)$.\n\n"
                    "**Integrals (Accumulation & Area)**:\n"
                    "- **Fundamental Theorem of Calculus**:\n"
                    "  $$\\int_a^b f(x)\\,dx = F(b) - F(a) \\quad \\text{where } F'(x) = f(x)$$\n"
                    "- **Integration by Parts**: $\\int u\\,dv = uv - \\int v\\,du$."
                ),
                "keywords": "calculus, derivative, integral, differentiation, integration, rate of change, math"
            },
            {
                "topic": "Bayes' Theorem & Probabilistic Inference",
                "category": "Mathematics",
                "summary": "Foundational theorem in probability determining the conditional probability of an event based on prior knowledge of related conditions.",
                "content": (
                    "**Mathematical Formulation**:\n"
                    "$$P(A|B) = \\frac{P(B|A) \\cdot P(A)}{P(B)}$$\n\n"
                    "**Components**:\n"
                    "- $P(A|B)$: **Posterior Probability** (belief after observing evidence $B$).\n"
                    "- $P(B|A)$: **Likelihood** (probability of evidence given hypothesis $A$).\n"
                    "- $P(A)$: **Prior Probability** (initial degree of belief).\n"
                    "- $P(B)$: **Marginal Likelihood / Evidence** (total probability of observing $B$).\n\n"
                    "**Applications**: Machine Learning (Naive Bayes), medical diagnosis testing, spam filters, Kalman filtering, Bayesian robotics."
                ),
                "keywords": "bayes theorem, probability, statistics, conditional probability, bayesian inference, math"
            },

            # -------------------------------------------------------------
            # Space Exploration & World History
            # -------------------------------------------------------------
            {
                "topic": "Apollo 11 & Lunar Exploration",
                "category": "History & Space Exploration",
                "summary": "Historic American spaceflight that first landed humans on the Moon on July 20, 1969.",
                "content": (
                    "**Key Highlights**:\n"
                    "- **Crew**: Commander Neil Armstrong, Lunar Module Pilot Buzz Aldrin, Command Module Pilot Michael Collins.\n"
                    "- **Launch Vehicle**: Saturn V rocket designed under Wernher von Braun, launched from Kennedy Space Center.\n"
                    "- **Lunar Module**: *Eagle* landed on the Sea of Tranquility (*Mare Tranquillitatis*).\n"
                    "- **Famous Quote**: 'That's one small step for [a] man, one giant leap for mankind.'\n"
                    "- **Significance**: Won the Cold War Space Race and proved humanity's capacity for interplanetary travel."
                ),
                "keywords": "apollo 11, moon landing, neil armstrong, buzz aldrin, space, nasa, history"
            },
            {
                "topic": "Chandrayaan-3 & Lunar South Pole Landing",
                "category": "History & Space Exploration",
                "summary": "ISRO's landmark lunar exploration mission that accomplished humanity's first successful soft landing near the Moon's South Pole.",
                "content": (
                    "**Mission Overview**:\n"
                    "- **Agency**: Indian Space Research Organisation (ISRO).\n"
                    "- **Landing Date**: August 23, 2023 at 18:04 IST.\n"
                    "- **Spacecraft**: Lander *Vikram* and Rover *Pragyan*.\n"
                    "- **Scientific Discovery**: In-situ confirmation of sulfur (S), aluminum, calcium, iron, titanium, and temperature gradient analysis of lunar topsoil.\n"
                    "- **National Space Day**: India declared August 23 as National Space Day in honor of this accomplishment."
                ),
                "keywords": "chandrayaan 3, isro, moon south pole, vikram lander, pragyan rover, space exploration"
            }
        ]

        inserted = 0
        for item in curriculum:
            res = self.teach_concept(
                topic=item["topic"],
                content=item["content"],
                category=item["category"],
                summary=item["summary"],
                keywords=item["keywords"],
                source="curated_pretrain",
                confidence=1.0
            )
            if res.get("status") == "success":
                inserted += 1

        logger.info(f"Successfully seeded {inserted} concepts into ARHIEA Knowledge Base.")
        return inserted

knowledge_engine = KnowledgeBaseEngine()
