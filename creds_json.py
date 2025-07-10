import json

with open("cred3.json") as f:
    data = json.load(f)
    print(json.dumps(data))
