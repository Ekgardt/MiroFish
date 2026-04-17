from pathlib import Path
import re
import json

ROOT = Path('/opt/mirofish/frontend')
FILES = list(ROOT.rglob('*.vue')) + list(ROOT.rglob('*.js')) + list(ROOT.rglob('*.html'))

CJK = re.compile(r'[\u4e00-\u9fff]')
ATTR_RE = re.compile(r'''(?P<attr>title|placeholder|aria-label|label|alt|content)=["'](?P<val>[^"']*[\u4e00-\u9fff][^"']*)["']''')
TEXT_RE = re.compile(r'>([^<>]*[\u4e00-\u9fff][^<>]*)<')
STR_RE = re.compile(r'''(?P<q>["'`])(?P<val>(?:(?!\1).)*[\u4e00-\u9fff](?:(?!\1).)*)\1''')

results = []
seen = set()

def add(file_path, line_no, kind, text, context):
    text = text.strip()
    if not text:
        return
    key = (str(file_path), line_no, kind, text)
    if key in seen:
        return
    seen.add(key)
    results.append({
        'file': str(file_path).replace('/opt/mirofish/', ''),
        'line': line_no,
        'kind': kind,
        'source': text,
        'context': context.rstrip('\n')
    })

for file_path in FILES:
    try:
        lines = file_path.read_text(encoding='utf-8').splitlines()
    except Exception:
        continue

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith('<!--') or stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
            continue

        if not CJK.search(line):
            continue

        for m in ATTR_RE.finditer(line):
            add(file_path, i, f"attr:{m.group('attr')}", m.group('val'), line)

        for m in TEXT_RE.finditer(line):
            add(file_path, i, 'text', m.group(1), line)

        for m in STR_RE.finditer(line):
            val = m.group('val')
            if CJK.search(val):
                add(file_path, i, 'string', val, line)

results.sort(key=lambda x: (x['file'], x['line'], x['kind'], x['source']))

out = Path('/opt/mirofish/ui_strings_source.jsonl')
with out.open('w', encoding='utf-8') as f:
    for row in results:
        f.write(json.dumps(row, ensure_ascii=False) + '\n')

print(f'Saved {len(results)} strings to {out}')
