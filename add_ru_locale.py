from pathlib import Path
import json
import shutil
import re

ROOT = Path("/opt/mirofish")
LOCALES = ROOT / "locales"

en_path = LOCALES / "en.json"
ru_path = LOCALES / "ru.json"
langs_path = LOCALES / "languages.json"
index_path = ROOT / "frontend" / "index.html"

en = json.loads(en_path.read_text(encoding="utf-8"))

# copy en -> ru as a base
ru = en.copy()

def deep_set(d, path, value):
    cur = d
    for key in path[:-1]:
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
    cur[path[-1]] = value

# Homepage / obvious visible strings from the user's screenshots and grep
overrides = {
    ("home", "visitGithub"): "Открыть нашу страницу на GitHub",
    ("home", "heroTitle1"): "Загрузите отчёты,",
    ("home", "heroTitle2"): "Предскажите будущее",
    ("home", "systemReady"): "Готово",
    ("home", "systemReadyDesc"): "Модуль прогнозирования в режиме ожидания. Загрузите неструктурированные данные, чтобы запустить сценарий симуляции.",
}

# Common English strings seen on the first screen / navigation
extra_overrides = {
    ("home", "ready"): "Готово",
    ("home", "simulationHistory", "title"): "История симуляций",
    ("history", "title"): "История симуляций",
}

for path, value in {**overrides, **extra_overrides}.items():
    deep_set(ru, path, value)

# save ru.json with backup if needed
if ru_path.exists():
    shutil.copy2(ru_path, ru_path.with_suffix(".json.bak"))
ru_path.write_text(json.dumps(ru, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# patch languages.json as robustly as possible
langs_raw = json.loads(langs_path.read_text(encoding="utf-8"))
changed_langs = False

if isinstance(langs_raw, list):
    codes = set()
    for item in langs_raw:
        if isinstance(item, dict):
            code = item.get("code") or item.get("value") or item.get("key")
            if code:
                codes.add(code)
    if "ru" not in codes:
        langs_raw.append({"code": "ru", "label": "Русский"})
        changed_langs = True

elif isinstance(langs_raw, dict):
    # case 1: mapping like {"en": "...", "zh": "..."}
    if all(isinstance(k, str) for k in langs_raw.keys()) and not any(isinstance(v, dict) for v in langs_raw.values()):
        if "ru" not in langs_raw:
            langs_raw["ru"] = "Русский"
            changed_langs = True
    # case 2: object with nested list
    elif "languages" in langs_raw and isinstance(langs_raw["languages"], list):
        codes = set()
        for item in langs_raw["languages"]:
            if isinstance(item, dict):
                code = item.get("code") or item.get("value") or item.get("key")
                if code:
                    codes.add(code)
        if "ru" not in codes:
            langs_raw["languages"].append({"code": "ru", "label": "Русский"})
            changed_langs = True

if changed_langs:
    shutil.copy2(langs_path, langs_path.with_suffix(".json.bak"))
    langs_path.write_text(json.dumps(langs_raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# set default locale in index.html from zh/en to ru where possible
if index_path.exists():
    original = index_path.read_text(encoding="utf-8")
    patched = original
    patched = patched.replace("localStorage.getItem('locale') || 'zh'", "localStorage.getItem('locale') || 'ru'")
    patched = patched.replace('localStorage.getItem("locale") || "zh"', 'localStorage.getItem("locale") || "ru"')
    patched = re.sub(r'<html lang="[^"]+">', '<html lang="ru">', patched, count=1)
    if patched != original:
        shutil.copy2(index_path, index_path.with_suffix(".html.bak.ru"))
        index_path.write_text(patched, encoding="utf-8")

print("Created/updated:")
print(" -", ru_path)
print(" -", langs_path)
print(" -", index_path)
print("Done.")
