import re
import logging
from typing import Dict, Any, Optional, Tuple
from backend.tools.registry import registry
from backend.services.vision import camera_service
from backend.services.visual_memory import visual_memory_engine
from backend.services.screen import screen_vision_service
from backend.services.shutdown import is_goodbye_request, perform_graceful_shutdown
from backend.services.routine_learner import routine_learner
from backend.agent.web_search import search_web_summary
from backend.tools.math_tools import evaluate_math_expression
from backend.tools.flight_tools import resolve_user_location
from backend.services.knowledge_engine import knowledge_engine

logger = logging.getLogger("ARHIEA.Router")

def extract_flight_details(text: str, default_origin: str, is_reply: bool = False) -> Dict[str, Any]:
    t = text.lower()
    site = None
    if "makemytrip" in t or "mmt" in t:
        site = "MakeMyTrip"
    elif "skyscanner" in t:
        site = "Skyscanner"
    elif "expedia" in t:
        site = "Expedia"
    elif "cleartrip" in t:
        site = "Cleartrip"
    elif "kayak" in t:
        site = "Kayak"
    elif "google flights" in t or "google flight" in t:
        site = "Google Flights"

    origin = default_origin
    from_match = re.search(r"\bfrom\s+([a-zA-Z\s]+?)(?:\s+to\b|\s+on\b|\s+tomorrow|\s+via\b|$)", t)
    if from_match:
        cand_origin = from_match.group(1).strip()
        if cand_origin in ["my given location", "my location", "here", "given location", "current location"]:
            origin = default_origin
        elif cand_origin and not any(w in cand_origin for w in ["flight", "ticket", "book"]):
            origin = cand_origin.title()

    dest = None
    to_match = re.search(r"\bto\s+([a-zA-Z\s]+?)(?:\s+on\b|\s+tomorrow|\s+today|\s+next\b|\s+via\b|\s+from\b|\s+on\s+google|\s+on\s+makemytrip|\s+on\s+skyscanner|$)", t)
    if to_match:
        cand_dest = to_match.group(1).strip()
        cand_dest = re.sub(r"\b(book|flight|tickets?|a|the|my|given|location)\b", "", cand_dest).strip()
        if cand_dest and len(cand_dest) > 1:
            dest = cand_dest.title()
    elif is_reply:
        clean = re.sub(r"\b(tomorrow|today|tonight|next\s+[a-zA-Z]+|on|in|via|makemytrip|google flights|skyscanner|expedia|cleartrip|kayak)\b.*", "", t).strip()
        clean = re.sub(r"^(to\s+|fly\s+to\s+)", "", clean).strip()
        if clean and len(clean) > 1 and not any(w in clean for w in ["flight", "ticket", "book", "location"]):
            dest = clean.title()

    date_str = None
    date_match = re.search(r"\b(tomorrow|day after tomorrow|today|tonight|next week|next [a-zA-Z]+|\d{1,2}(?:st|nd|rd|th)?\s+[a-zA-Z]+(?:\s+\d{4})?|[a-zA-Z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?|\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|on [a-zA-Z]+)\b", t)
    if date_match:
        date_str = date_match.group(1).strip()
        if date_str.startswith("on "):
            date_str = date_str[3:].strip()

    return {"origin": origin, "destination": dest, "date": date_str, "site": site}

class FastDeterministicRouter:
    """Zero-latency local routing for deterministic tasks, system clock, camera, apps, maps, youtube, reminders, flights."""

    def __init__(self):
        self.pending_flight: Optional[Dict[str, Any]] = None

    async def route_and_execute(self, user_input: str) -> Optional[Dict[str, Any]]:
        raw_text = user_input.strip()
        t = raw_text.lower().rstrip(".!?,")

        # 0. Flight Booking Multi-Turn Continuation
        if self.pending_flight:
            # Step A: User was asked "Where would you like to fly to from {origin}, and on what date?"
            if self.pending_flight.get("step") == "awaiting_destination_date":
                origin = self.pending_flight.get("origin") or resolve_user_location()
                details = extract_flight_details(raw_text, default_origin=origin, is_reply=True)
                dest = details["destination"]
                date = details["date"] or "tomorrow"
                site = details["site"]

                if dest:
                    if site:
                        self.pending_flight = None
                        tool_res = await registry.execute(
                            "book_flight_tickets",
                            {"destination": dest, "origin": origin, "date": date, "preferred_site": site}
                        )
                        res_data = tool_res.get("result", {})
                        return {
                            "handled": True,
                            "response": res_data.get("message", f"Redirecting to {site} for flights from {origin} to {dest}."),
                            "action": "open_url",
                            "url": res_data.get("url"),
                            "booking_data": res_data.get("booking_data"),
                            "tool": "book_flight_tickets",
                            "verified": True
                        }
                    else:
                        self.pending_flight = {
                            "step": "awaiting_site",
                            "origin": origin,
                            "destination": dest,
                            "date": date
                        }
                        return {
                            "handled": True,
                            "response": f"From which booking site would you like to book your flight from {origin} to {dest}? (Google Flights, MakeMyTrip, Skyscanner, or Expedia)",
                            "tool": "book_flight_tickets",
                            "pending_flight": self.pending_flight,
                            "booking_data": {
                                "origin": origin,
                                "destination": dest,
                                "date": date,
                                "awaiting_site": True
                            },
                            "verified": True
                        }

            # Step B: User was asked "From which booking site would you like to book?"
            elif self.pending_flight.get("step") == "awaiting_site":
                origin = self.pending_flight.get("origin") or resolve_user_location()
                dest = self.pending_flight.get("destination") or "Delhi"
                date = self.pending_flight.get("date") or "tomorrow"

                site = "Google Flights"
                if "make" in t or "mmt" in t:
                    site = "MakeMyTrip"
                elif "sky" in t:
                    site = "Skyscanner"
                elif "expedia" in t:
                    site = "Expedia"
                elif "clear" in t:
                    site = "Cleartrip"
                elif "kayak" in t:
                    site = "Kayak"
                elif "google" in t or "any" in t or "first" in t or "preferred" in t:
                    site = "Google Flights"

                self.pending_flight = None
                tool_res = await registry.execute(
                    "book_flight_tickets",
                    {"destination": dest, "origin": origin, "date": date, "preferred_site": site}
                )
                res_data = tool_res.get("result", {})
                return {
                    "handled": True,
                    "response": res_data.get("message", f"Redirecting to {site} for flights from {origin} to {dest}."),
                    "action": "open_url",
                    "url": res_data.get("url"),
                    "booking_data": res_data.get("booking_data"),
                    "tool": "book_flight_tickets",
                    "verified": True
                }

        # 0. Natural Chat-Based Learning & Memory Ingestion
        teach_res = knowledge_engine.detect_and_learn_from_chat(raw_text)
        if teach_res:
            return {
                "handled": True,
                "response": teach_res["response"],
                "tool": "teach_concept",
                "verified": True
            }

        # =====================================================================
        # 0.5 CRITICAL ROAD & MEDICAL EMERGENCY FAST-RESPONSE (<2ms)
        # =====================================================================
        # A: Immediate Emergency SOS Trigger
        if re.search(r"\b(emergency sos|send sos|trigger sos|call emergency|call 112|call 911|call ambulance|i need help urgently|send help|emergency alert)\b", t):
            tool_res = await registry.execute("trigger_emergency_sos", {
                "incident_description": raw_text,
                "severity": "CRITICAL"
            })
            res_data = tool_res.get("result", {})
            formatted_text = (
                f"🚨 **EMERGENCY SOS DISPATCH INITIATED!**\n\n"
                f"**Location**: {res_data.get('location')}\n"
                f"**Coordinates**: {res_data.get('coordinates', {}).get('lat')}, {res_data.get('coordinates', {}).get('lon')}\n"
                f"**Incident Summary**: {raw_text}\n"
                f"**Emergency Report**: Saved to `{res_data.get('report_saved_to')}`\n\n"
                f"### **Verified Emergency Hotlines (Call Immediately)**:\n"
                f"- **National All-in-One Emergency**: **112** (India / EU) | **911** (US)\n"
                f"- **Ambulance / Medical Response**: **108**\n"
                f"- **Police Dispatch**: **100**\n"
                f"- **National Highway Patrol (NHAI)**: **1073**\n\n"
                f"> [!IMPORTANT]\n"
                f"> Stay on the line with 112. An official incident report with your medical profile has been saved to your Desktop."
            )
            return {
                "handled": True,
                "response": formatted_text,
                "tool": "trigger_emergency_sos",
                "emergency_data": res_data,
                "action": "emergency_alert",
                "verified": True
            }

        # B: Vehicle Crisis: Brake Failure
        if re.search(r"\b(brake(s)? (failed|not working|stopped working|broken|gone)|car won'?t stop|cannot stop car|how to stop without brakes)\b", t):
            tool_res = await registry.execute("get_emergency_protocol", {"emergency_type": "brake_failure"})
            res_data = tool_res.get("result", {})
            resp = (
                f"🚨 **VEHICLE BRAKE FAILURE EMERGENCY PROTOCOL**\n\n"
                f"> [!CAUTION]\n> **DO NOT TURN OFF YOUR ENGINE.** Turning off the ignition locks your steering wheel!\n\n"
                f"### **Immediate Action Steps**:\n"
                f"1. **Pump the Brake Pedal Rapidly**: Dual-split hydraulic lines may rebuild pressure after 3–4 firm pumps.\n"
                f"2. **Downshift Progressively (Engine Braking)**: Shift sequentially (5th -> 4th -> 3rd -> 2nd -> 1st) to force the engine compression to slow you down.\n"
                f"3. **Apply Emergency Handbrake Gently**: Below 40 km/h, pull the handbrake lever gradually while holding the ratchet release button to avoid locking rear wheels.\n"
                f"4. **Seek Soft Runoff Friction**: Steer towards gravel shoulders, grass verges, or gentle upward slopes.\n"
                f"5. **Alert Surroundings**: Switch on hazard warning flashers and sound your horn continuously to warn other motorists."
            )
            return {
                "handled": True,
                "response": resp,
                "tool": "get_emergency_protocol",
                "emergency_data": res_data,
                "action": "emergency_alert",
                "verified": True
            }

        # C: Vehicle Crisis: Aquaplaning / Hydroplaning
        if re.search(r"\b(aquaplaning|hydroplaning|car skidding on water|sliding on wet road|skidding in rain)\b", t):
            tool_res = await registry.execute("get_emergency_protocol", {"emergency_type": "aquaplaning"})
            res_data = tool_res.get("result", {})
            resp = (
                f"🌊 **AQUAPLANING / HYDROPLANING RECOVERY PROTOCOL**\n\n"
                f"> [!CAUTION]\n> **DO NOT SLAM THE BRAKES.** Abrupt braking will cause the vehicle to spin out of control!\n\n"
                f"### **Recovery Steps**:\n"
                f"1. **Ease Off Accelerator Smoothly**: Remove your foot from the gas pedal to let aerodynamic drag and rolling friction decelerate the car.\n"
                f"2. **Hold Steering Wheel Straight**: Keep the wheels aligned with the road direction. Avoid sudden jerky counter-steering.\n"
                f"3. **Wait for Tread to Bite Water**: As vehicle momentum drops, tyre grooves will disperse the water layer and restore tarmac grip.\n"
                f"4. **Post-Recovery**: Reduce speed by at least 20 km/h and maintain a 4-second following distance."
            )
            return {
                "handled": True,
                "response": resp,
                "tool": "get_emergency_protocol",
                "emergency_data": res_data,
                "action": "emergency_alert",
                "verified": True
            }

        # D: Vehicle Crisis: Tyre Blowout
        if re.search(r"\b(tyre (burst|blowout|punctured)|tire (burst|blowout|exploded)|flat tyre at speed)\b", t):
            tool_res = await registry.execute("get_emergency_protocol", {"emergency_type": "tyre_blowout"})
            res_data = tool_res.get("result", {})
            resp = (
                f"⚠️ **HIGH-SPEED TYRE BLOWOUT PROTOCOL**\n\n"
                f"> [!CAUTION]\n> **DO NOT SLAM BRAKES.** Hard braking shifts weight onto the compromised rim, risking a rollover!\n\n"
                f"### **Stabilization Steps**:\n"
                f"1. **Grip Steering Wheel with Both Hands**: Expect a violent sideways pull towards the flat tyre. Counter-steer firmly to maintain straight path.\n"
                f"2. **Tap Accelerator Briefly, Then Coast**: Stabilize vehicle inertia, then ease off throttle and let deceleration happen naturally.\n"
                f"3. **Indicate & Pull Safely Off Highway**: Once under 30 km/h, brake softly, activate hazard warning lights, and park on the hard shoulder.\n"
                f"4. **Place Warning Triangle 50m Behind Car**: Ensure all passengers exit on the non-traffic side and stand behind crash barriers."
            )
            return {
                "handled": True,
                "response": resp,
                "tool": "get_emergency_protocol",
                "emergency_data": res_data,
                "action": "emergency_alert",
                "verified": True
            }

        # E: Medical Crisis: CPR Protocol
        if re.search(r"\b(cpr|cardiac arrest|heart stopped|how to do cpr|start cpr|resuscitation|chest compressions|how to perform cpr)\b", t):
            tool_res = await registry.execute("get_emergency_protocol", {"emergency_type": "cpr"})
            res_data = tool_res.get("result", {})
            resp = (
                f"❤️ **ADULT CARDIOPULMONARY RESUSCITATION (CPR) PROTOCOL**\n\n"
                f"> [!IMPORTANT]\n> **Call 112 / 108 (India) or 911 (US) immediately.** Put speakerphone on and ask for an AED.\n\n"
                f"### **Life-Saving Steps**:\n"
                f"1. **Check Responsiveness**: Tap shoulders firmly and shout 'Are you okay?'. Check for normal breathing (max 10 seconds).\n"
                f"2. **Hand Position**: Place heel of one hand in the center of the chest (lower half of breastbone). Interlock other hand on top.\n"
                f"3. **Compression Depth & Rhythm**: Push **hard and fast** (5–6 cm depth) at **100–120 compressions per minute** (cadence of *'Stayin Alive'*).\n"
                f"4. **30 Compressions : 2 Breaths**: Perform 30 high-quality compressions, tilt head back, pinch nose, deliver 2 gentle 1-second rescue breaths.\n"
                f"5. **Hands-Only CPR**: If untrained or uncomfortable giving breaths, perform **continuous uninterrupted chest compressions** until paramedics arrive."
            )
            return {
                "handled": True,
                "response": resp,
                "tool": "get_emergency_protocol",
                "emergency_data": res_data,
                "action": "emergency_alert",
                "verified": True
            }

        # F: Medical Crisis: Choking & Heimlich
        if re.search(r"\b(choking|heimlich|someone is choking|airway blocked|can'?t breathe food)\b", t):
            tool_res = await registry.execute("get_emergency_protocol", {"emergency_type": "choking_heimlich"})
            res_data = tool_res.get("result", {})
            resp = (
                f"🚨 **CHOKING RELIEF / HEIMLICH MANEUVER PROTOCOL**\n\n"
                f"1. **Confirm Complete Choking**: Ask 'Are you choking?'. If they cannot speak, cough, or breathe, act immediately.\n"
                f"2. **5 Back Blows**: Lean victim forward, deliver 5 sharp blows with heel of your hand between shoulder blades.\n"
                f"3. **5 Abdominal Thrusts (Heimlich)**: Stand behind victim, place thumb side of fist slightly above navel (below ribcage), grasp fist with other hand, pull sharply **inward and upward**.\n"
                f"4. **Repeat 5 & 5 Cycle**: Alternate 5 back blows and 5 abdominal thrusts until object is dislodged.\n"
                f"5. **If Victim Becomes Unresponsive**: Lower safely to floor, call 112 / 108, and begin chest compressions (CPR) immediately."
            )
            return {
                "handled": True,
                "response": resp,
                "tool": "get_emergency_protocol",
                "emergency_data": res_data,
                "action": "emergency_alert",
                "verified": True
            }

        # G: Medical Crisis: Severe Burns
        if re.search(r"\b(burns|severe burn|burned my (hand|arm|skin)|hot water burn|fire burn|chemical burn)\b", t):
            tool_res = await registry.execute("get_emergency_protocol", {"emergency_type": "burns"})
            res_data = tool_res.get("result", {})
            resp = (
                f"🔥 **THERMAL & CHEMICAL BURNS FIRST AID PROTOCOL**\n\n"
                f"> [!CAUTION]\n> **DO NOT USE ICE, BUTTER, OR OILS.** Ice damages tissue; oils trap heat inside the dermis.\n\n"
                f"1. **Cool with Running Water for 20 Minutes**: Run gentle, cool tap water over burn immediately. Do not stop early.\n"
                f"2. **Remove Constrictive Items**: Take off rings, watches, and tight clothing before tissue swelling occurs.\n"
                f"3. **Never Pop Blisters**: Intact blisters are a natural sterile barrier against severe bacterial infection.\n"
                f"4. **Cover Loosely**: Wrap loosely with clean plastic cling film or sterile non-adherent dressing.\n"
                f"5. **Seek Emergency Care (112/108)**: For burns larger than a palm, charred/white skin, or burns to face, hands, or joints."
            )
            return {
                "handled": True,
                "response": resp,
                "tool": "get_emergency_protocol",
                "emergency_data": res_data,
                "action": "emergency_alert",
                "verified": True
            }

        # H: Medical Crisis: Severe Bleeding
        if re.search(r"\b(severe bleeding|heavy bleeding|tourniquet|arterial bleeding|blood not stopping|deep cut bleeding)\b", t):
            tool_res = await registry.execute("get_emergency_protocol", {"emergency_type": "severe_bleeding"})
            res_data = tool_res.get("result", {})
            resp = (
                f"🩸 **SEVERE BLEEDING & TOURNIQUET APPLICATION PROTOCOL**\n\n"
                f"1. **Continuous Direct Pressure**: Press clean cloth or sterile dressing directly onto wound with both hands. Add more layers if soaked.\n"
                f"2. **Elevate Wound**: Elevate bleeding limb above heart level (unless fracture suspected).\n"
                f"3. **Tourniquet for Severe Limb Arterial Bleeding**: Place tourniquet 2–3 inches above wound (between wound and heart). Never place over joints.\n"
                f"4. **Tighten Until Bleeding Ceases**: Wind the rod until bright red spurting ceases, lock in place, and **note the exact time applied** on the patient's forehead or bandage.\n"
                f"5. **Prevent Shock**: Lay victim flat, keep warm with blanket, do not give food/drink, and dial 112 / 108 immediately."
            )
            return {
                "handled": True,
                "response": resp,
                "tool": "get_emergency_protocol",
                "emergency_data": res_data,
                "action": "emergency_alert",
                "verified": True
            }

        # I: General Road Accident Triage
        if re.search(r"\b(car crash|road accident|i was in an accident|accident happened|hit a car|crash reported|golden hour)\b", t):
            tool_res = await registry.execute("get_emergency_protocol", {"emergency_type": "road_accident"})
            res_data = tool_res.get("result", {})
            resp = (
                f"🚑 **ROAD ACCIDENT GOLDEN HOUR PROTOCOL**\n\n"
                f"> [!IMPORTANT]\n> The first 60 minutes following trauma dictate survival rates. Act deliberately.\n\n"
                f"1. **Secure the Scene First**: Switch on hazard flashers, place warning triangles, turn off ignitions to eliminate fire hazards.\n"
                f"2. **Call Emergency Services (112 / 108)**: Report exact location, number of injured passengers, and vehicle hazards.\n"
                f"3. **Do NOT Move Injured Casualties (C-Spine)**: Unless immediate fire or submersion hazard exists, keep victim's neck and spine strictly aligned.\n"
                f"4. **Assess ABC (Airway, Breathing, Circulation)**: Clear mouth obstructions, ensure chest rise, and apply firm direct pressure to heavy bleeding.\n"
                f"5. **Keep Calm & Warm**: Talk reassuringly, cover victims with blankets to prevent hypothermia, and await emergency services."
            )
            return {
                "handled": True,
                "response": resp,
                "tool": "get_emergency_protocol",
                "emergency_data": res_data,
                "action": "emergency_alert",
                "verified": True
            }

        # 1. Goodbye / Self Shutdown
        if is_goodbye_request(t):
            res = await perform_graceful_shutdown()
            return {
                "handled": True,
                "response": res["message"],
                "action": "exit_app",
                "tool": "shutdown",
                "verified": True
            }

        # 2. Conversational Greetings & Banter (Instant Response)
        if re.search(r"^(hello|hi|hey|hey arhiea|hello arhiea|hi arhiea|hey aegis|hello aegis|hi aegis|hey aura|hello aura|hi aura|greetings|good morning|good afternoon|good evening|yo)\b", t):
            if "morning" in t:
                greet = "Good morning! I'm here and ready to help. What are we working on today?"
            elif "evening" in t:
                greet = "Good evening! How can I assist you tonight?"
            elif "afternoon" in t:
                greet = "Good afternoon! What can I do for you?"
            else:
                greet = "Hey! I'm here. What can I do for you?"
            return {"handled": True, "response": greet, "tool": "greeting", "verified": True}

        if re.search(r"\b(how are you|how are you doing|what's up|how's it going|how are you today)\b", t):
            return {
                "handled": True,
                "response": "I'm doing great, thanks for asking! What are we working on today?",
                "tool": "conversation",
                "verified": True
            }

        if re.search(r"\b(who are you|what is your name|introduce yourself|tell me about yourself)\b", t):
            return {
                "handled": True,
                "response": "I am ARHIEA — your Adaptive Road and Human Intelligence Emergency System for Windows. I can control your PC, launch apps, draw in Paint, manage reminders, inspect your environment via camera, solve mathematics, and automate your daily tasks.",
                "tool": "identity",
                "verified": True
            }

        if re.search(r"\b(tell me something interesting|tell me a fun fact|give me a fact|fun fact)\b", t):
            return {
                "handled": True,
                "response": "Sure! Did you know that honey never spoils? Archaeologists have found 3,000-year-old pots of honey in ancient Egyptian tombs that are still perfectly edible.",
                "tool": "fun_fact",
                "verified": True
            }

        if re.search(r"\b(thank you|thanks|thanks arhiea|thank you arhiea|thanks aegis|thank you aegis|thanks aura|thank you aura|great job|awesome)\b", t):
            return {
                "handled": True,
                "response": "You're very welcome! Let me know if you need anything else.",
                "tool": "politeness",
                "verified": True
            }

        if re.search(r"^(help|what can you do|what can i say|commands)\b", t):
            return {
                "handled": True,
                "response": "You can talk to me naturally! Try saying 'What is the time right now?', '2*2', 'Open Chrome', 'Open Paint and draw a house', 'Play Believer on YouTube', 'Where is the clock?', or 'Remind me tomorrow at 5 PM'.",
                "tool": "help",
                "verified": True
            }

        # 3. Mathematical Problems & Arithmetic Evaluation (<1ms)
        is_math_candidate = bool(
            re.search(r"(\d+\s*[\+\-\*\/\%\^\×\÷]\s*\d+|\d+\s*x\s*\d+|\d+\s*%\s+of\s+\d+|sqrt\(\d+|cbrt\(\d+|\b(sin|cos|tan|log|factorial)\(\d+)", t) or
            re.search(r"^(calculate|solve|evaluate|how much is|what is \d+|what's \d+)\b", t) or
            re.search(r"\b(\d+\s+(?:plus|minus|times|multiplied by|divided by)\s+\d+)\b", t) or
            re.search(r"\b(gcd|lcm|hcf|prime|factors? of|prime factorization|factorial|npr|ncr|permutation|combination)\b", t) or
            re.search(r"\b(mean|median|mode|variance|standard deviation|hypotenuse|pythagorean)\b", t) or
            re.search(r"\b(area of (a |the )?(circle|rectangle|triangle)|circumference of (a |the )?circle)\b", t) or
            re.search(r"\b(celsius to fahrenheit|fahrenheit to celsius|km to miles|miles to km|kg to lbs|lbs to kg)\b", t) or
            re.search(r"\b(increase|decrease)\s+\d+(\.\d+)?\s*%\b", t) or
            re.search(r"\b(derivative|differentiate|differentiation|diff\b|integral|integrate|integration|antiderivative|calculus|d\/dx|limit of|lim\s+x)\b", t) or
            re.search(r"\b(dot product|vector|magnitude of|determinant|det of|matrix|log base|log_\d+|log2\b|log10\b)\b", t) or
            re.search(r"(\b[a-z]\b|\d+).*=.*(\b[a-z]\b|\d+)", t) or
            re.match(r"^[\d\s\+\-\*\/\(\)\.\^\%x=]+$", t)
        )
        if is_math_candidate and not any(w in t for w in ["time", "date", "reminder", "remind", "camera", "youtube", "directions", "map", "pm", "am"]):
            math_res = evaluate_math_expression(raw_text)
            if math_res.get("success") or "Division by zero" in math_res.get("message", ""):
                return {
                    "handled": True,
                    "response": math_res["message"],
                    "tool": "calculate_math",
                    "verified": True
                }

        # 4. Real Windows System Clock & Date (Universal matching)
        if re.search(r"\b(what('s| is)? (the )?time( right now| now)?|current time|tell me (the )?time|what time( is it)?( right now)?|time right now|time now|the time right now)\b", t) or t in ["time", "time please", "what time", "what is time", "the time"]:
            tool_res = await registry.execute("get_system_time", {})
            msg = tool_res.get("result", {}).get("message", "The time is available.")
            return {"handled": True, "response": msg, "tool": "get_system_time", "verified": True}

        if re.search(r"\b(what date is today|what's today's date|today's date|what day is today|what date is it|what is the date|tell me the date)\b", t) or t in ["date", "today's date", "what date"]:
            tool_res = await registry.execute("get_system_date", {})
            msg = tool_res.get("result", {}).get("message", "Today's date is available.")
            return {"handled": True, "response": msg, "tool": "get_system_date", "verified": True}

        # 5. Camera Controls & Status
        if re.search(r"\b(turn on( the)? camera|start( the)? camera|enable( the)? camera|enable continuous camera)\b", t):
            continuous = "continuous" in t or "24/7" in t
            res = camera_service.start_camera(continuous=continuous)
            return {"handled": True, "response": "Camera is active.", "tool": "start_camera", "verified": True}

        if re.search(r"\b(turn off( the)? camera|stop( the)? camera|disable( the)? camera|close( the)? camera)\b", t):
            res = camera_service.stop_camera()
            return {"handled": True, "response": "Camera is turned off.", "tool": "stop_camera", "verified": True}

        if re.search(r"\b(pause( the)? camera)\b", t):
            res = camera_service.pause_camera()
            return {"handled": True, "response": "Camera paused.", "tool": "pause_camera", "verified": True}

        if re.search(r"\b(resume( the)? camera)\b", t):
            res = camera_service.resume_camera()
            return {"handled": True, "response": "Camera resumed.", "tool": "resume_camera", "verified": True}

        if re.search(r"\b(is there a person|detect person|any person in front|check if someone is there|is someone there)\b", t):
            res = camera_service.detect_person_local()
            return {"handled": True, "response": res["message"], "tool": "detect_person", "data": res, "verified": True}

        # 5. Immediate Camera Environment Perception
        if re.search(
            r"\b(what am i looking at|what do you see|describe what you see|what's in front of me|"
            r"what is in front of the camera|what is this object|look at this|what do you see in front of the camera|"
            r"what's in front of the camera|detect (?:the )?objects?|identify (?:the )?objects?|identify (?:the )?items?|"
            r"identify this|what objects do you see|what objects are (?:here|there|in front)|what is in my hand|"
            r"what am i holding|scan (?:the )?room|scan (?:the )?surroundings|recognize (?:the )?objects?|"
            r"check (?:the )?objects?|what is this|look around)\b",
            t
        ):
            if not camera_service.is_active:
                # Try auto-activating or prompt user
                res_start = camera_service.start_camera()
                if not camera_service.is_active:
                    return {
                        "handled": True,
                        "response": "The camera is currently turned off. Please enable the camera so I can see your surroundings.",
                        "tool": "vision_notice",
                        "verified": True
                    }
            res = await visual_memory_engine.analyze_frame_and_extract_memory()
            return {"handled": True, "response": res.get("message", "I have analyzed your surroundings."), "tool": "analyze_camera", "verified": True}

        # 6. Visual Memory Spatial Queries
        if re.search(
            r"\b(where (?:is|are|was|did you see|did i (?:leave|put|keep)|can i find)(?: my| the)?|"
            r"have you seen(?: my| the)?|did you see(?: my| the)?|find(?: my| the)?|locate(?: my| the)?|"
            r"what is next to(?: my| the)?|what room am i in|what was on the table|what was beside)\b",
            t
        ):
            mem_res = visual_memory_engine.query_object_location(t)
            # If not found in previous memory, but camera is active, analyze the live frame right now
            if not mem_res.get("found", False) and camera_service.is_active:
                await visual_memory_engine.analyze_frame_and_extract_memory()
                mem_res = visual_memory_engine.query_object_location(t)
            return {"handled": True, "response": mem_res["message"], "tool": "query_visual_memory", "data": mem_res, "verified": True}

        # 7. Screen Perception
        if re.search(r"\b(what is on my screen|read this error|what does this error mean|read what's on my screen|look at my screen)\b", t):
            res = await screen_vision_service.analyze_screen_content(t)
            return {"handled": True, "response": res.get("message", "Screen analyzed."), "tool": "analyze_screen", "verified": True}

        # 8. Direct YouTube Video & Music Playback
        yt_play_match = re.search(r"\b(?:play|stream|listen to)\s+(.+?)(?:\s+on youtube|\s+video|\s+song)?$", raw_text, re.IGNORECASE)
        if yt_play_match and not any(w in t for w in ["game", "video game", "audio file", "paint", "flight"]):
            target_media = yt_play_match.group(1).strip()
            clean_media = re.sub(r"^(the\s+song\s+|the\s+video\s+|the\s+track\s+|song\s+|video\s+|track\s+)", "", target_media, flags=re.IGNORECASE).strip()
            tool_res = await registry.execute("youtube_play", {"song": clean_media or target_media})
            res_data = tool_res.get("result", {})
            routine_learner.log_action("website_open", "YouTube")
            return {
                "handled": True,
                "response": res_data.get("message", f"Playing {clean_media} on YouTube."),
                "action": res_data.get("action", "open_url"),
                "url": res_data.get("url"),
                "media_data": res_data.get("media_data"),
                "tool": "youtube_play",
                "verified": True
            }

        # 10. Google Maps & Directions
        directions_match = re.search(r"\b(?:show|give me|get)?\s*directions (?:from\s+(.+?)\s+)?to\s+(.+)$", raw_text, re.IGNORECASE)
        if directions_match:
            origin = directions_match.group(1) or "Current Location"
            destination = directions_match.group(2).strip()
            tool_res = await registry.execute("maps_directions", {"destination": destination, "origin": origin})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", f"Showing directions to {destination} on Google Maps.")
            routine_learner.log_action("website_open", "Google Maps")
            return {"handled": True, "response": msg, "tool": "maps_directions", "verified": True}

        maps_search_match = re.search(r"\b(?:show|open)\s+(.+?)\s+on (?:google )?maps\b", raw_text, re.IGNORECASE)
        if maps_search_match or t == "open google maps" or t == "open maps":
            query = maps_search_match.group(1).strip() if maps_search_match else "Google Maps"
            if query.lower() == "google maps":
                tool_res = await registry.execute("open_website", {"url": "https://maps.google.com"})
                msg = "Google Maps is open."
            else:
                tool_res = await registry.execute("open_maps", {"query": query})
                msg = f"Showing {query} on Google Maps."
        # 11. Context-Aware Flight Booking & Portal Redirection
        if (
            re.search(r"\b(book|reserve|find|search)\s+(?:a\s+)?(?:flight|air\s*ticket|flight\s*ticket|plane\s*ticket|tickets?)\b", t) or
            "book flight" in t or
            "flight booking" in t or
            re.search(r"\bflight(?:s)?\s+(?:from|to)\b", t)
        ):
            origin_loc = resolve_user_location()
            details = extract_flight_details(raw_text, default_origin=origin_loc, is_reply=False)
            origin = details["origin"]
            dest = details["destination"]
            date = details["date"] or "tomorrow"
            site = details["site"]

            if not dest:
                self.pending_flight = {
                    "step": "awaiting_destination_date",
                    "origin": origin
                }
                return {
                    "handled": True,
                    "response": f"Where would you like to fly to from {origin}, and on what date? (I can book via Google Flights, MakeMyTrip, Skyscanner, or Expedia.)",
                    "tool": "book_flight_tickets",
                    "pending_flight": self.pending_flight,
                    "booking_data": {"origin": origin, "awaiting_destination": True},
                    "verified": True
                }

            if not site:
                self.pending_flight = {
                    "step": "awaiting_site",
                    "origin": origin,
                    "destination": dest,
                    "date": date
                }
                return {
                    "handled": True,
                    "response": f"From which site would you like to book your flight from {origin} to {dest} on {date}? (Google Flights, MakeMyTrip, Skyscanner, or Expedia)",
                    "tool": "book_flight_tickets",
                    "pending_flight": self.pending_flight,
                    "booking_data": {
                        "origin": origin,
                        "destination": dest,
                        "date": date,
                        "awaiting_site": True
                    },
                    "verified": True
                }

            # Everything provided in one command!
            self.pending_flight = None
            tool_res = await registry.execute(
                "book_flight_tickets",
                {"destination": dest, "origin": origin, "date": date, "preferred_site": site}
            )
            res_data = tool_res.get("result", {})
            return {
                "handled": True,
                "response": res_data.get("message", f"Redirecting to {site} for flights from {origin} to {dest}."),
                "action": "open_url",
                "url": res_data.get("url"),
                "booking_data": res_data.get("booking_data"),
                "tool": "book_flight_tickets",
                "verified": True
            }

        # 12. Reminders (Universal Robust Matching)
        if re.search(r"\b(list my reminders|show( all)? reminders|what are my reminders|check reminders)\b", t):
            tool_res = await registry.execute("list_reminders", {})
            msg = tool_res.get("result", {}).get("message", "You have no active reminders.")
            return {"handled": True, "response": msg, "tool": "list_reminders", "verified": True}

        if re.search(r"\b(cancel( my)? reminder|delete( my)? reminder|remove reminder)\b", t):
            query = t.replace("cancel my reminder", "").replace("delete my reminder", "").replace("cancel reminder", "").strip() or "all"
            tool_res = await registry.execute("delete_reminder", {"query": query})
            msg = tool_res.get("result", {}).get("message", "Reminder cancelled.")
            return {"handled": True, "response": msg, "tool": "delete_reminder", "verified": True}

        # Pattern A: "remind me at 5 PM to submit assignment" OR "set reminder for 5 PM to submit assignment"
        p_at_to = re.search(r"\b(?:set a reminder|remind me)\s+(?:for |at |in )?(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|tomorrow(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?|today(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?|\d+\s+minutes?|\d+\s+hours?)\s+(?:to\s+|about\s+|for\s+)(.+)$", t)
        if p_at_to:
            time_str = p_at_to.group(1).strip()
            text_str = p_at_to.group(2).strip()
            tool_res = await registry.execute("create_reminder", {"text": text_str, "time_str": time_str})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", "Reminder scheduled.")
            return {"handled": True, "response": msg, "tool": "create_reminder", "verified": tool_res.get("verified", False)}

        # Pattern B: "remind me to submit assignment at 5 PM" OR "set a reminder to sleep tomorrow at 12:07 AM"
        p_to_at = re.search(r"\b(?:set a reminder|remind me)\s+(?:to\s+|about\s+|for\s+)?(.+?)\s+(?:at\s+|on\s+|in\s+|tomorrow\s*at\s*|tomorrow\s+|today\s*at\s*)(\d{1,2}(?::\d{2})?\s*(?:am|pm)?|tomorrow(?:\s+at\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?)?|\d+\s+minutes?|\d+\s+hours?)$", t)
        if p_to_at:
            text_str = p_to_at.group(1).strip()
            time_str = p_to_at.group(2).strip()
            if "tomorrow" in t and "tomorrow" not in time_str:
                time_str = f"tomorrow at {time_str}"
            tool_res = await registry.execute("create_reminder", {"text": text_str, "time_str": time_str})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", "Reminder scheduled.")
            return {"handled": True, "response": msg, "tool": "create_reminder", "verified": tool_res.get("verified", False)}

        # Pattern C: "remind me tomorrow at 5 PM to submit assignment"
        reminder_time_match = re.search(r"\b(?:set a )?remind(?:er)?(?: me)?\s+(?:for\s+)?(tomorrow.+?|today.+?|in \d+.+?|at \d+.+?|on [a-zA-Z]+.+?)\s+to\s+(.+)$", t)
        if reminder_time_match:
            time_str = reminder_time_match.group(1).strip()
            text_str = reminder_time_match.group(2).strip()
            tool_res = await registry.execute("create_reminder", {"text": text_str, "time_str": time_str})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", "Reminder scheduled.")
            return {"handled": True, "response": msg, "tool": "create_reminder", "verified": tool_res.get("verified", False)}

        # Pattern D: Remind me without time -> SIH Rule: ask "When should I remind you?"
        if re.search(r"\b(?:remind me|set a reminder|set reminder)\b", t):
            task_text = re.sub(r"\b(remind me to|remind me about|set a reminder to|set reminder to|remind me|set a reminder)\s*", "", t).strip()
            return {
                "handled": True,
                "response": "When should I remind you?",
                "tool": "create_reminder",
                "pending_reminder_task": task_text or "your task",
                "verified": True
            }

        # 12. Application and Website Launching
        if t.startswith("open ") or t.startswith("launch ") or t.startswith("start "):
            target = re.sub(r"^(open|launch|start)\s+", "", t).strip()
            
            if target in ["youtube", "google", "github", "wikipedia", "reddit", "twitter"]:
                url = f"https://{target}.com"
                tool_res = await registry.execute("open_website", {"url": url})
                routine_learner.log_action("website_open", target.capitalize())
                return {"handled": True, "response": f"Done. {target.capitalize()} is open.", "tool": "open_website", "verified": True}

            tool_res = await registry.execute("open_application", {"app_name": target})
            res_data = tool_res.get("result", {})
            msg = res_data.get("message", f"Done. {target.capitalize()} is open.")
            routine_learner.log_action("app_launch", target)
            return {"handled": True, "response": msg, "tool": "open_application", "verified": tool_res.get("verified", False)}

        if t.startswith("close ") or t.startswith("quit ") or t.startswith("exit "):
            target = re.sub(r"^(close|quit|exit)\s+", "", t).strip()
            tool_res = await registry.execute("close_application", {"app_name": target})
            msg = tool_res.get("result", {}).get("message", f"Closed {target}.")
            return {"handled": True, "response": msg, "tool": "close_application", "verified": tool_res.get("verified", False)}

        # 13. Volume Adjustments
        if "volume up" in t or "increase volume" in t:
            await registry.execute("set_volume", {"action": "up"})
            return {"handled": True, "response": "Volume increased.", "tool": "set_volume", "verified": True}
        if "volume down" in t or "decrease volume" in t:
            await registry.execute("set_volume", {"action": "down"})
            return {"handled": True, "response": "Volume decreased.", "tool": "set_volume", "verified": True}
        if "mute" in t or "unmute" in t:
            await registry.execute("set_volume", {"action": "mute"})
            return {"handled": True, "response": "Volume toggled.", "tool": "set_volume", "verified": True}

        return None

router = FastDeterministicRouter()
