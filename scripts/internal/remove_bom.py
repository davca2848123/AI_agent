#!/usr/bin/env python3
"""Remove BOM from commands.py"""

# Remove BOM from commands.py
with open('agent/commands.py', 'rb') as f:
    content = f.read()

# Remove UTF-8 BOM if present
if content.startswith(b'\xef\xbb\xbf'):
    content = content[3:]
    with open('agent/commands.py', 'wb') as f:
        f.write(content)
    print('✅ BOM removed')
else:
    print('⚠️ No BOM found')

# Verify syntax
with open('agent/commands.py', 'r', encoding='utf-8') as f:
    code = f.read()

try:
    compile(code, 'agent/commands.py', 'exec')
    print('✅ Syntax check passed!')
except SyntaxError as e:
    print(f'❌ Syntax error at line {e.lineno}: {e.msg}')
