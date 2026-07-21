import json, re, glob
from collections import defaultdict
import requests

# --- 1. Build gazetteer from characters.json ---
with open("data/characters.json", encoding="utf-8") as f:
    characters = json.load(f)

spells = requests.get("https://hp-api.onrender.com/api/spells").json()

# hardcoded supplement: places & creatures (hp-api doesn't cover these)
places = ["Hogwarts", "Diagon Alley", "The Burrow", "Privet Drive", "Hogsmeade",
          "Gryffindor", "Slytherin", "Ravenclaw", "Hufflepuff", "Azkaban",
          "Forbidden Forest", "Knockturn Alley", "Ministry of Magic", "Godric's Hollow"]
creatures = ["Dementor", "Basilisk", "Hippogriff", "Dobby", "Fawkes", "Buckbeak",
             "Nagini", "Aragog", "Fluffy", "Troll", "Werewolf", "Centaur"]

entities = {}  # id -> {name, type, attrs}
alias_to_id = {}

first_counts, last_counts = defaultdict(int), defaultdict(int)
for c in characters:
    parts = c["name"].split()
    if len(parts) > 1:
        first_counts[parts[0]] += 1
        last_counts[parts[-1]] += 1

for c in characters:
    if not c.get("name"):
        continue
    eid = c["id"]
    entities[eid] = {"name": c["name"], "type": "character",
                      "house": c.get("house") or None, "species": c.get("species") or None}
    names = {c["name"]} | {a for a in c.get("alternate_names", []) if a}
    parts = c["name"].split()
    if len(parts) > 1:
        if first_counts[parts[0]] == 1:
            names.add(parts[0])
        if last_counts[parts[-1]] == 1:
            names.add(parts[-1])
    for n in names:
        if len(n) >= 3 and n not in alias_to_id:
            alias_to_id[n] = eid

for s in spells:
    if not s.get("name"):
        continue
    eid = "spell_" + s["name"]
    entities[eid] = {"name": s["name"], "type": "spell", "effect": s.get("description")}
    alias_to_id[s["name"]] = eid

for p in places:
    eid = "place_" + p
    entities[eid] = {"name": p, "type": "place"}
    alias_to_id[p] = eid

for cr in creatures:
    eid = "creature_" + cr
    entities[eid] = {"name": cr, "type": "creature"}
    alias_to_id[cr] = eid

# --- 2. Compile matcher ---
aliases_sorted = sorted(alias_to_id.keys(), key=len, reverse=True)
pattern = re.compile(r"\b(" + "|".join(re.escape(a) for a in aliases_sorted) + r")\b")

def find_entities(text):
    return [(m.start(), m.end(), alias_to_id[m.group(1)]) for m in pattern.finditer(text)]

# --- 3. Process books: co-occurrence + dialogue attribution ---
co_occurrence = defaultdict(lambda: defaultdict(int))
dialogue = defaultdict(int)
quote_pattern = re.compile(r'"([^"]{3,300})"')

for path in sorted(glob.glob("data/book*.txt")):
    book = path.split("/")[-1].replace(".txt", "")
    text = open(path, encoding="utf-8", errors="ignore").read()

    # co-occurrence per paragraph
    for para in re.split(r"\n\s*\n", text):
        found = {eid for _, _, eid in find_entities(para)}
        found = list(found)
        for i in range(len(found)):
            for j in range(i + 1, len(found)):
                a, b = sorted([found[i], found[j]])
                co_occurrence[(a, b, book)]["weight"] += 1 if isinstance(co_occurrence[(a,b,book)], dict) else 1

    # dialogue attribution
    for qm in quote_pattern.finditer(text):
        window_start = max(0, qm.start() - 80)
        window_end = min(len(text), qm.end() + 80)
        window = text[window_start:window_end]
        nearby = [(abs((s + window_start) - qm.start()), eid)
                  for s, e, eid in find_entities(window)
                  if entities[eid]["type"] == "character"]
        if nearby:
            nearby.sort()
            speaker = nearby[0][1]
            dialogue[(speaker, book)] += 1

    print(book, "done")

# --- 4. Save ---
co_list = [{"source": a, "target": b, "book": book, "weight": d["weight"]}
           for (a, b, book), d in co_occurrence.items()]
dia_list = [{"character": c, "book": book, "lines": n} for (c, book), n in dialogue.items()]

with open("data/entities.json", "w", encoding="utf-8") as f:
    json.dump(entities, f, indent=2)
with open("data/co_occurrence.json", "w", encoding="utf-8") as f:
    json.dump(co_list, f, indent=2)
with open("data/dialogue.json", "w", encoding="utf-8") as f:
    json.dump(dia_list, f, indent=2)

print("Entities:", len(entities))
print("Co-occurrence edges:", len(co_list))
print("Dialogue records:", len(dia_list))