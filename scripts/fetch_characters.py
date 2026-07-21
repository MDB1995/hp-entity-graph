import requests, json

chars = requests.get("https://hp-api.onrender.com/api/characters").json()
with open("data/characters.json", "w") as f:
    json.dump(chars, f, indent=2)

print(len(chars), "characters")
print(chars[0])