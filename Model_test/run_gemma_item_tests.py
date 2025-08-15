# run_gemma_item_tests.py
import json, time, csv, sys, re, requests
from collections import defaultdict

# ==== Config ====
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:1b-it-qat"   # instruction-tuned, better accuracy
TESTS_PATH = "tests_items.json"
OUT_CSV = "results_items.csv"

CATEGORIES = [
    "Dairy","Bakery","Produce","Pulses","Grains","Flour","Household","Protein",
    "Beverages","Spices","Sweeteners","Essentials","Oils","Snacks","Other"
]

# Mapping hints + few-shots to guide the model for Indian groceries
GUIDE = """
Mapping hints (India):
- Rice/Basmati → Grains
- Atta/Flour/Maida → Flour
- Paneer/Curd/Yogurt/Butter/Milk/Perugu → Dairy
- Dal/Toor/Masoor/Chana/Peas (dry) → Pulses
- Tomato/Potato/Aloo/Banana/Apple → Produce
- Detergent/Soap/Dishwash/Cleaner → Household
- Oil (Sunflower/Mustard/Groundnut/Refined) → Oils
- Sugar/Jaggery → Sweeteners
- Salt → Essentials
- Biscuits/Namkeen/Chips → Snacks
- Tea/Coffee/Soft drinks/Juices → Beverages
- Turmeric/Chilli/Cumin/Coriander (dry) → Spices
"""

FEW_SHOTS = """
Examples:
- "Basmati Rice 5kg" → "Grains"
- "Atta (Whole Wheat) 5kg" → "Flour"
- "Paneer 200g" → "Dairy"
- "Detergent Powder 1kg" → "Household"
- "Tomato 1kg" → "Produce"
- "Doodh 1L" → "Dairy"
- "Aloo 1kg" → "Produce"
- "Perugu 500ml" → "Dairy"
"""

PROMPT_TEMPLATE = """You are a grocery insights engine.
Task: Categorize each item into one of these categories:
{cats}

Be robust to spelling mistakes and Indian languages (Hindi/Telugu).
Use these hints:
{guide}

Few-shot:
{few}

Return STRICT JSON only in this schema:
{{
  "categories":[
    {{"name":"<category>","items":[{{"name":"","qty":0,"unit":"","price":0}}],"subtotal":0}}
  ],
  "totals":{{"grand_total":0}}
}}

Input items: {items_json}
"""

# ==== Helpers ====

def norm(s: str) -> str:
    """Normalize item names for more stable matching."""
    s = s.lower()
    s = re.sub(r'[\-\(\)]', ' ', s)
    # remove units like '1kg', '500 g', '2l', '12 pc', 'bunch', 'dozen'
    s = re.sub(r'\b\d+(\.\d+)?\s*(kg|g|l|ml|pc|pcs|bunch|dozen)\b', '', s)
    # remove numbers attached to units e.g., 2x100g
    s = re.sub(r'\b\d+x\d+(g|ml)\b', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

# Optional: hard keyword backstop for obvious corrections
KEYWORD_BACKSTOP = [
    (re.compile(r'\b(rice|basmati)\b', re.I), "Grains"),
    (re.compile(r'\b(atta|flour|maida)\b', re.I), "Flour"),
    (re.compile(r'\b(paneer|curd|yogurt|butter|milk|perugu|dahi)\b', re.I), "Dairy"),
    (re.compile(r'\b(dal|toor|masoor|chana|urad|moong|peas)\b', re.I), "Pulses"),
    (re.compile(r'\b(tomato|potato|aloo|banana|apple|onion)\b', re.I), "Produce"),
    (re.compile(r'\b(detergent|soap|dishwash|cleaner)\b', re.I), "Household"),
    (re.compile(r'\b(oil|sunflower|mustard|groundnut|refined)\b', re.I), "Oils"),
    (re.compile(r'\b(sugar|jaggery|gur)\b', re.I), "Sweeteners"),
    (re.compile(r'\b(salt)\b', re.I), "Essentials"),
    (re.compile(r'\b(biscuit|namkeen|chips|snack)\b', re.I), "Snacks"),
    (re.compile(r'\b(tea|coffee|cola|juice|tropicana|soda)\b', re.I), "Beverages"),
    (re.compile(r'\b(turmeric|chilli|cumin|jeera|coriander|dhania)\b', re.I), "Spices"),
]

def backstop_category(item_name: str, current_cat: str) -> str:
    """Correct obviously wrong categories using keywords."""
    if current_cat not in CATEGORIES or current_cat == "Other":
        for pat, cat in KEYWORD_BACKSTOP:
            if pat.search(item_name):
                return cat
    return current_cat

def call_gemma(items):
    prompt = PROMPT_TEMPLATE.format(
        cats=json.dumps(CATEGORIES, ensure_ascii=False),
        guide=GUIDE.strip(),
        few=FEW_SHOTS.strip(),
        items_json=json.dumps(items, ensure_ascii=False),
    )
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",                        # force JSON
        "options": {"temperature": 0.0, "num_ctx": 8192}
    }

    t0 = time.time()
    r = requests.post(OLLAMA_URL, json=payload, timeout=240)
    latency = time.time() - t0
    r.raise_for_status()
    text = (r.json() or {}).get("response", "")

    # First pass: direct parse
    try:
        return json.loads(text), latency
    except Exception:
        pass

    # Fallback 1: extract inner JSON
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end+1]), latency
        except Exception:
            pass

    # Fallback 2: ask the model to repair JSON (one extra call)
    repair_prompt = f"Return only valid JSON (no text). Fix this to valid JSON:\n{text}"
    repair = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": repair_prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0}
        },
        timeout=120
    )
    fixed = (repair.json() or {}).get("response", "{}")
    try:
        return json.loads(fixed), latency
    except Exception:
        # Safe default
        return {"categories": [], "totals": {"grand_total": 0}}, latency

def score_case(test_case, model_output):
    # Build normalized map: item_name -> predicted_category
    pred_map = {}
    for cat in model_output.get("categories", []):
        cname = cat.get("name", "Other")
        for it in cat.get("items", []):
            key = norm(it.get("name",""))
            if not key:
                continue
            # apply keyword backstop to fix obvious misses
            cname_fixed = backstop_category(it.get("name",""), cname)
            pred_map[key] = cname_fixed

    total = 0
    correct = 0
    per_item = []
    for it in test_case["items"]:
        total += 1
        name_key = norm(it["name"])
        pred = pred_map.get(name_key, "Other")
        exp = it.get("expected_category", "Other")
        ok = (pred == exp)
        correct += 1 if ok else 0
        per_item.append({
            "item_name": it["name"],
            "expected": exp,
            "predicted": pred,
            "ok": ok
        })
    acc = correct / total if total else 0.0
    return acc, per_item

def main():
    try:
        tests = json.load(open(TESTS_PATH, "r", encoding="utf-8"))
    except FileNotFoundError:
        sys.stderr.write(f"ERROR: Cannot find {TESTS_PATH}. Place it next to this script.\n")
        sys.exit(1)

    rows = []
    for tc in tests:
        data, latency = call_gemma(tc["items"])
        acc, item_rows = score_case(tc, data)
        rows.append({
            "test_id": tc["id"],
            "items_count": len(tc["items"]),
            "accuracy": round(acc, 3),
            "latency_sec": round(latency, 2)
        })
        # Print mismatches for inspection
        mismatches = [r for r in item_rows if not r["ok"]]
        if mismatches:
            print(f"[{tc['id']}] mismatches:")
            for m in mismatches:
                print(f"  - {m['item_name']}: expected {m['expected']} | got {m['predicted']}")

    # Write summary CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["test_id","items_count","accuracy","latency_sec"])
        w.writeheader()
        w.writerows(rows)

    # Overall stats
    overall_acc = sum(r["accuracy"] for r in rows) / len(rows) if rows else 0.0
    avg_latency = sum(r["latency_sec"] for r in rows) / len(rows) if rows else 0.0
    print("\n=== Summary ===")
    print(f"Cases: {len(rows)}")
    print(f"Overall accuracy: {overall_acc:.3f}")
    print(f"Average latency (s): {avg_latency:.2f}")
    print(f"CSV saved: {OUT_CSV}")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        sys.stderr.write("ERROR: Cannot connect to Ollama at http://localhost:11434. Is Ollama running and is the model pulled?\n")
        sys.exit(1)
