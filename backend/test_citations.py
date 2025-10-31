#!/usr/bin/env python3
"""
Quick test script to verify citation format in composition.
Run this to test if citations are working.
"""

import sys
import json
from app.services.llm import compose_outline_essay

# Test data
test_nodes = [
    {"id": "n1", "text": "Four-day workweeks reduce employee burnout", "type": "CLAIM"},
    {"id": "n2", "text": "Employees reported 40% less emotional exhaustion", "type": "EVIDENCE"},
    {"id": "n3", "text": "Productivity levels remained constant or improved", "type": "EVIDENCE"},
]

test_edges = [
    {"from_id": "n2", "to_id": "n1", "relation": "SUPPORTS"},
    {"from_id": "n3", "to_id": "n1", "relation": "SUPPORTS"},
]

print("Testing composition with citations...")
print("=" * 80)

result, used_llm = compose_outline_essay(
    thesis="A four-day workweek improves employee wellbeing without reducing productivity",
    nodes=test_nodes,
    edges=test_edges,
    words=300,
    audience="general",
    tone="neutral"
)

print(f"\nLLM Used: {used_llm}")
print(f"\nOutline:")
print(json.dumps(result.get("outline", []), indent=2))

print(f"\n{'='*80}")
print("Essay (clean version):")
print("=" * 80)
print(result.get("essay_md", "No essay generated"))

print(f"\n{'='*80}")
print("Essay with Citations:")
print("=" * 80)
essay_with_citations = result.get("essay_with_citations", "No cited essay generated")
print(essay_with_citations)

# Check for citation warnings
if "_citation_warnings" in result:
    print(f"\n{'='*80}")
    print("⚠️  CITATION WARNINGS:")
    print("=" * 80)
    for warning in result["_citation_warnings"]:
        print(f"  - {warning}")

# Validate citation format
import re
correct_citations = re.findall(r'\[Evidence:\s*"[^"]+"\]', essay_with_citations)
print(f"\n{'='*80}")
print(f"Found {len(correct_citations)} correctly formatted citations")
if correct_citations:
    print("Examples:")
    for citation in correct_citations[:3]:
        print(f"  ✓ {citation}")
else:
    print("  ⚠️  No citations in correct format [Evidence: \"quote\"] found!")

print("=" * 80)
