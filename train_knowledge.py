#!/usr/bin/env python3
"""
ARHIEA Knowledge Trainer & Brain Ingestion CLI
Usage:
  python train_knowledge.py --seed
  python train_knowledge.py --stats
  python train_knowledge.py --file path/to/document.txt --category "Computer Science"
  python train_knowledge.py --query "What is CPR?"
  python train_knowledge.py --teach "Topic" "Detailed explanation of concept..."
"""

import sys
import os
import argparse
import json

# Ensure parent directory is in Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from backend.services.knowledge_engine import knowledge_engine

def main():
    parser = argparse.ArgumentParser(description="ARHIEA AI Knowledge Trainer & Learning Pipeline")
    parser.add_argument("--seed", action="store_true", help="Pre-train and seed the foundational AI curriculum")
    parser.add_argument("--force-seed", action="store_true", help="Force re-seeding even if already initialized")
    parser.add_argument("--stats", action="store_true", help="Display brain knowledge telemetry")
    parser.add_argument("--file", type=str, help="Path to text or markdown file to ingest and learn")
    parser.add_argument("--category", type=str, default="Document Trained", help="Category for learned concepts")
    parser.add_argument("--query", type=str, help="Query the AI brain to test knowledge recall")
    parser.add_argument("--teach", nargs=2, metavar=("TOPIC", "CONTENT"), help="Teach a specific concept: --teach <Topic> <Content>")

    args = parser.parse_args()

    if args.seed or args.force_seed:
        print("[+] Training ARHIEA AI Brain with foundational curriculum...")
        count = knowledge_engine.seed_default_knowledge(force=args.force_seed)
        print(f"[✓] Completed! Brain now contains active concepts.")
        stats = knowledge_engine.get_stats()
        print(f"[*] Telemetry: {json.dumps(stats, indent=2)}")
        return

    if args.stats:
        stats = knowledge_engine.get_stats()
        print("=" * 60)
        print("  ARHIEA NEURAL KNOWLEDGE BASE TELEMETRY")
        print("=" * 60)
        print(f"Total Concepts Learned : {stats['total_concepts']}")
        print(f"Last Trained           : {stats['last_trained']}")
        print("\nDomain Categories Breakdown:")
        for cat, cnt in stats["categories"].items():
            print(f"  - {cat:<30}: {cnt} concepts")
        print("\nKnowledge Sources:")
        for src, cnt in stats["sources"].items():
            print(f"  - {src:<30}: {cnt}")
        print("=" * 60)
        return

    if args.file:
        file_path = os.path.abspath(args.file)
        if not os.path.exists(file_path):
            print(f"[-] Error: File not found at '{file_path}'")
            sys.exit(1)

        print(f"[+] Training AI on document: {file_path} ...")
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        res = knowledge_engine.train_from_text(content, category=args.category)
        print(f"[✓] Training finished! Learned {res['concepts_learned']} concepts:")
        for t in res.get("topics", []):
            print(f"  * {t}")
        return

    if args.teach:
        topic, content = args.teach
        print(f"[+] Teaching AI concept '{topic}' ...")
        res = knowledge_engine.teach_concept(topic, content, category=args.category)
        print(f"[✓] {res}")
        return

    if args.query:
        print(f"[*] Searching AI Brain for '{args.query}' ...")
        results = knowledge_engine.search_knowledge(args.query, limit=2)
        if not results:
            print("[-] No matching concepts in learned knowledge base.")
        else:
            for r in results:
                print("\n" + "=" * 60)
                print(f"TOPIC: {r['topic']} (Relevance: {r['relevance_score']}) | Category: {r['category']}")
                print("-" * 60)
                print(r["content"])
                print("=" * 60)
        return

    parser.print_help()

if __name__ == "__main__":
    main()
