from pathlib import Path
import json
import shutil

ROOT = Path("/opt/mirofish")
MAP_FILE = ROOT / "ui_strings_ru.jsonl"

rows = [json.loads(line) for line in MAP_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]

# group replacements per file
by_file = {}
for row in rows:
    src = row["source"]
    tgt = row["target"]
    if src == tgt:
        continue
    by_file.setdefault(row["file"], [])
    pair = (src, tgt)
    if pair not in by_file[row["file"]]:
        by_file[row["file"]].append(pair)

changed = []
for rel_file, pairs in by_file.items():
    path = ROOT / rel_file
    if not path.exists():
        print(f"SKIP missing: {rel_file}")
        continue

    text = path.read_text(encoding="utf-8")
    new_text = text

    # longest-first reduces partial replacement issues
    for src, tgt in sorted(pairs, key=lambda p: len(p[0]), reverse=True):
        new_text = new_text.replace(src, tgt)

    if new_text != text:
        backup = path.with_suffix(path.suffix + ".bak.ru")
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(new_text, encoding="utf-8")
        changed.append(rel_file)

print("Changed files:")
for item in changed:
    print(" -", item)
print(f"Total changed: {len(changed)}")
