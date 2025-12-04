import os
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DOCS_DIR = r"z:\rpi_ai\rpi_ai\documentation"

def audit_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    filename = os.path.basename(filepath)
    rel_path = os.path.relpath(filepath, DOCS_DIR)
    
    issues = []
    
    # 1. Check Navigation Header
    # Expecting > **Navigace:** on line 3 (index 2) or similar, usually after H1
    has_nav = False
    for i in range(min(10, len(lines))):
        if lines[i].strip().startswith("> **Navigace:**"):
            has_nav = True
            break
    
    if not has_nav:
        issues.append(f"Missing Navigation Header")

    # 2. Check Anchors for Headings (H2, H3)
    # Pattern: Look for lines starting with ## or ###
    # Check if previous non-empty line is <a name="..."></a>
    
    for i, line in enumerate(lines):
        if line.startswith("##"):
            # It's a heading
            heading_level = len(line.split()[0])
            heading_text = line.strip().lstrip("#").strip()
            
            # Check previous lines for anchor
            has_anchor = False
            j = i - 1
            while j >= 0:
                prev_line = lines[j].strip()
                if prev_line == "":
                    j -= 1
                    continue
                
                if re.match(r'<a name="[\w-]+"></a>', prev_line):
                    has_anchor = True
                break
            
            if not has_anchor:
                issues.append(f"Missing anchor for {heading_level} heading: '{heading_text}' at line {i+1}")

    return issues

def main():
    print(f"Auditing documentation in {DOCS_DIR}...\n")
    
    total_issues = 0
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                issues = audit_file(filepath)
                
                if issues:
                    print(f"FILE: {os.path.relpath(filepath, DOCS_DIR)}")
                    for issue in issues:
                        print(f"  - {issue}")
                    print()
                    total_issues += len(issues)

    if total_issues == 0:
        print("✅ No issues found! All files have navigation and anchors.")
    else:
        print(f"❌ Found {total_issues} issues.")

if __name__ == "__main__":
    main()
