from pathlib import Path
import csv, io, json, requests

OUT = Path("/app/data/jailbreakbench_official.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

if OUT.exists():
    print(f"Official JailbreakBench already present: {OUT}")
    raise SystemExit(0)

URLS = [
    ("harmful", "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/resolve/main/data/harmful-behaviors.csv"),
    ("benign", "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/resolve/main/data/benign-behaviors.csv"),
]

rows = []
for label, url in URLS:
    print(f"Downloading official JailbreakBench {label} split...")
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    text = r.content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    for i, item in enumerate(reader):
        goal = (item.get("Goal") or "").strip()
        if not goal:
            continue
        rows.append({
            "id": f"jbb-{label}-{item.get('Index', i)}",
            "category": label,
            "prompt": goal,
            "behavior": (item.get("Behavior") or "").strip(),
            "topic": (item.get("Category") or "").strip(),
            "source": (item.get("Source") or "").strip(),
        })

if not rows:
    raise RuntimeError("Official JailbreakBench download succeeded but no rows were parsed.")

OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Saved {len(rows)} official JailbreakBench rows to {OUT}")
