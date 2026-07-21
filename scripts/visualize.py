import json, math
import networkx as nx
from pyvis.network import Network

G = nx.read_graphml("data/graph.graphml")

HOUSE_COLORS = {
    "Gryffindor": "#740001", "Slytherin": "#1a472a",
    "Ravenclaw": "#0e1a40", "Hufflepuff": "#ecb939",
}
TYPE_COLORS = {"place": "#2a9d8f", "spell": "#9d4edd", "creature": "#e76f51"}

net = Network(height="100vh", width="100%", bgcolor="#111318", font_color="white", notebook=False)
net.force_atlas_2based(gravity=-60, spring_length=100)

degree = dict(G.degree(weight="weight"))

for n, data in G.nodes(data=True):
    d = degree.get(n, 1)
    size = 8 + 10 * math.log(d + 1)
    ntype = data.get("type", "character")
    if ntype == "character":
        color = HOUSE_COLORS.get(data.get("house"), "#888888")
    else:
        color = TYPE_COLORS.get(ntype, "#cccccc")
    title = f"{data.get('name')} ({ntype})"
    if data.get("house"):
        title += f" — {data['house']}"
    if data.get("lines_spoken"):
        title += f"<br>Lines spoken: {data['lines_spoken']}"
    if data.get("effect"):
        title += f"<br>{data['effect']}"
    title += f"<br>Connections weight: {d}"
    net.add_node(n, label=data.get("name", n), title=title, color=color, size=size,
                 group=data.get("community", 0))

for u, v, data in G.edges(data=True):
    net.add_edge(u, v, value=data.get("weight", 1), title=f"co-occurs {data.get('weight')}x")

net.set_options("""
{
  "interaction": { "hover": true, "tooltipDelay": 100 },
  "physics": { "stabilization": { "iterations": 150 } }
}
""")

net.write_html("report.html")
print("Wrote report.html")