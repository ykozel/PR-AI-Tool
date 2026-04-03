#!/usr/bin/env python3
"""
Batch add section type indicators to all scenario functions in the generator.
This script reads the generator file and inserts add_section_type() calls
before heading sections that don't already have them.
"""

import re

# Read the generator file with explicit encoding
with open("generate_test_dataset_comprehensive.py", "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Mapping of heading patterns to section types
# Format: (heading_text, section_type) tuples
heading_mappings = [
    (r'add_heading\(doc, "Summary", 2\)', 'add_section_type(doc, "SUMMARY")\n    add_heading(doc, "Summary", 2)'),
    (r'add_heading\(doc, "Performance Summary", 2\)', 'add_section_type(doc, "PERFORMANCE METRICS")\n    add_heading(doc, "Performance Summary", 2)'),
    (r'add_heading\(doc, "Performance Metrics", 2\)', 'add_section_type(doc, "PERFORMANCE METRICS")\n    add_heading(doc, "Performance Metrics", 2)'),
    (r'add_heading\(doc, "Feedback", 2\)', 'add_section_type(doc, "MANAGER FEEDBACK")\n    add_heading(doc, "Feedback", 2)'),
    (r'add_heading\(doc, "Development Gaps"', 'add_section_type(doc, "DEVELOPMENT AREAS")\n    add_heading(doc, "Development Gaps"'),
    (r'add_heading\(doc, "Strengths", 2\)', 'add_section_type(doc, "KEY ACHIEVEMENTS")\n    add_heading(doc, "Strengths", 2)'),
    (r'add_heading\(doc, "Key Strengths", 2\)', 'add_section_type(doc, "KEY ACHIEVEMENTS")\n    add_heading(doc, "Key Strengths", 2)'),
    (r'add_heading\(doc, "Concerns"', 'add_section_type(doc, "CONCERNS")\n    add_heading(doc, "Concerns"'),
    (r'add_heading\(doc, "Development Plan"', 'add_section_type(doc, "PDP - PROFESSIONAL DEVELOPMENT")\n    add_heading(doc, "Development Plan"'),
    (r'add_heading\(doc, "Skills', 'add_section_type(doc, "SKILLS & CERTIFICATION")\n    add_heading(doc, "Skills'),
    (r'add_heading\(doc, "Training"', 'add_section_type(doc, "TRAINING COMPLETED")\n    add_heading(doc, "Training"'),
    (r'add_heading\(doc, "Goals', 'add_section_type(doc, "GOALS")\n    add_heading(doc, "Goals'),
    (r'add_heading\(doc, "Self-Assessment"', 'add_section_type(doc, "SELF-ASSESSMENT")\n    add_heading(doc, "Self-Assessment"'),
    (r'add_heading\(doc, "Promotions?"', 'add_section_type(doc, "PROMOTION")\n    add_heading(doc, "Promotion"'),
    (r'add_heading\(doc, "Manager Recommendation"', 'add_section_type(doc, "RECOMMENDATIONS")\n    add_heading(doc, "Manager Recommendation"'),
    (r'add_heading\(doc, "Recommended Next Steps"', 'add_section_type(doc, "RECOMMENDATIONS")\n    add_heading(doc, "Recommended Next Steps"'),
    (r'add_heading\(doc, "Achievements"', 'add_section_type(doc, "KEY ACHIEVEMENTS")\n    add_heading(doc, "Achievements"'),
]

# Count changes
changes = 0

# Process each mapping
for pattern, replacement in heading_mappings:
    # Find all matches and count before filtering those already with section types
    matches = list(re.finditer(pattern, content))
    
    for match in reversed(matches):  # Process in reverse to maintain positions
        # Check if there's already an add_section_type() call right before this
        pos = match.start()
        # Look back 50 chars to see if add_section_type is already there
        context_before = content[max(0, pos-100):pos]
        
        if "add_section_type" not in context_before:
            # Insert the add_section_type call
            content = content[:pos] + replacement + content[pos + len(match.group()):]
            changes += 1

print(f"\n✅ Added section type indicators to {changes} headings")
print(f"   This ensures consistent tagging across all scenario functions")

# Write back with explicit encoding
with open("generate_test_dataset_comprehensive.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\n✅ Updated generator file successfully")
print("   Run 'python generate_test_dataset_comprehensive.py' to regenerate documents with section types")
