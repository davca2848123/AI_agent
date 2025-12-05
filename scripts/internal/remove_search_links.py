import os
import re

docs_dir = 'documentation'
pattern = r' \| \[🔍 Hledat\]\([^)]+\)'
files_changed = 0

for root, dirs, files in os.walk(docs_dir):
    for f in files:
        if f.endswith('.md'):
            file_path = os.path.join(root, f)
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                new_content = re.sub(pattern, '', content)
                
                if content != new_content:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(new_content)
                    files_changed += 1
                    print(f'Updated: {file_path}')
            except Exception as e:
                print(f'Error processing {file_path}: {e}')

print(f'\nTotal files updated: {files_changed}')
