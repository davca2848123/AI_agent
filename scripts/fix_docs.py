import os
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DOCS_DIR = r"z:\rpi_ai\rpi_ai\documentation"

def slugify(text):
    # Convert to lowercase
    text = text.lower()
    # Remove emojis and special chars (keep alphanumeric and spaces)
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with hyphens
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    modified = False
    
    for i, line in enumerate(lines):
        # Check for headings (##, ###, etc.)
        # But ignore the footer lines or horizontal rules
        if line.strip().startswith('#') and not line.strip().startswith('---'):
            # Determine heading level and text
            match = re.match(r'^(#+)\s+(.*)', line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2)
                
                # Skip H1 (Title) usually doesn't need anchor or has it differently
                if level > 1:
                    slug = slugify(text)
                    anchor_line = f'<a name="{slug}"></a>\n'
                    
                    # Check if previous line is already this anchor
                    has_anchor = False
                    if new_lines:
                        prev_line = new_lines[-1].strip()
                        if prev_line == anchor_line.strip():
                            has_anchor = True
                        # Check if previous line is empty and line before is anchor
                        elif prev_line == "" and len(new_lines) > 1:
                             if new_lines[-2].strip() == anchor_line.strip():
                                 has_anchor = True

                    if not has_anchor:
                        # Add anchor
                        # Ensure empty line before anchor if not at start
                        if new_lines and new_lines[-1].strip() != "":
                            new_lines.append("\n")
                        
                        new_lines.append(anchor_line)
                        modified = True
                        # print(f"  + Added anchor '{slug}' for '{text}'")

        new_lines.append(line)

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    return False

def main():
    print(f"Fixing documentation in {DOCS_DIR}...\n")
    
    count = 0
    for root, dirs, files in os.walk(DOCS_DIR):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    print(f"Fixed: {os.path.relpath(filepath, DOCS_DIR)}")
                    count += 1

    print(f"\n✅ Fixed anchors in {count} files.")

if __name__ == "__main__":
    main()
