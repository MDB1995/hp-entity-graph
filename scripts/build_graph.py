import json, networkx as nx
from networkx.algorithms.community import greedy_modularity_communities
from collections import defaultdict

with open("data/entities.json", encoding="utf-8") as f:
    entities = json.load(f)
with open("data/co_occurrence.json", encoding="utf-8") as f:
    co_occurrence = json.load(f)
with open("data/dialogue.json", encoding="utf-8") as f:
    dialogue = json.load(f)

# --- aggregate weights across books ---
edge_weight = defaultdict(int)
edge_books = defaultdict(set)
for row in co_occurrence:
    key = (row["source"], row["target"])
    edge_weight[key] += row["weight"]
    edge_books[key].add(row["book"])

lines_spoken = defaultdict(int)
for row in dialogue:
    lines_spoken[row["character"]] += row["lines"]

# --- build graph (filter weak edges for a readable viz) ---
G = nx.Graph()
for eid, data in entities.items():
    G.add_node(eid, **{k: v for k, v in data.items() if v is not None},
               lines_spoken=lines_spoken.get(eid, 0))

MIN_WEIGHT = 3
for (a, b), w in edge_weight.items():
    if w >= MIN_WEIGHT and a in entities and b in entities:
        G.add_edge(a, b, weight=w, books=len(edge_books[(a, b)]))

# drop isolated nodes (no strong edges) to keep the viz clean
G.remove_nodes_from(list(nx.isolates(G)))

print("Nodes:", G.number_of_nodes(), "Edges:", G.number_of_edges())

# --- insights ---
degree = dict(G.degree(weight="weight"))
top_connected = sorted(degree.items(), key=lambda x: -x[1])[:10]
print("\nTop 10 most connected entities:")
for eid, d in top_connected:
    print(f"  {entities[eid]['name']} ({entities[eid]['type']}): {d}")

communities = list(greedy_modularity_communities(G, weight="weight"))
print(f"\nDetected {len(communities)} communities")
for i, com in enumerate(communities[:6]):
    names = [entities[n]["name"] for n in com if entities[n]["type"] == "character"][:8]
    print(f"  Community {i}: {names}")

top_talkers = sorted(lines_spoken.items(), key=lambda x: -x[1])[:10]
print("\nTop 10 characters by dialogue lines:")
for eid, n in top_talkers:
    if eid in entities:
        print(f"  {entities[eid]['name']}: {n}")

# --- save for visualization + README stats ---
for i, com in enumerate(communities):
    for n in com:
        G.nodes[n]["community"] = i

nx.write_graphml(G, "data/graph.graphml")
with open("data/graph_nodelink.json", "w", encoding="utf-8") as f:
    json.dump(nx.node_link_data(G), f, indent=2)

print("\nSaved data/graph.graphml and data/graph_nodelink.json")

# --- house purity of communities (surprising insight check) ---
from collections import Counter
print("\nHouse composition per community:")
for i, com in enumerate(communities):
    houses = [entities[n].get("house") for n in com if entities[n]["type"] == "character" and entities[n].get("house")]
    if houses:
        counts = Counter(houses)
        total = sum(counts.values())
        top_house, top_n = counts.most_common(1)[0]
        purity = top_n / total
        print(f"  Community {i}: {dict(counts)}  purity={purity:.0%} ({total} sorted characters)")