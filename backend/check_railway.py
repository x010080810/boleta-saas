import urllib.request, json

TOKEN = "5INjqA0AHoHnxrBPzmj04MkHJDAVgBqc8fuTyBmhKIdwLPEuLqJ5E3KCL28JZzLF"
PROJECT_ID = "8dcc73cf-4512-464a-8ff4-3e951924f101"

query = """query {
  project(id: "%s") {
    services { id name }
    environments { name }
  }
}""" % PROJECT_ID

q = json.dumps({"query": query}).encode()

req = urllib.request.Request(
    "https://backboard.railway.app/graphql/v2",
    data=q,
    headers={
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "application/json",
    },
)
try:
    r = urllib.request.urlopen(req, timeout=10)
    print(json.dumps(json.loads(r.read()), indent=2))
except Exception as e:
    print("Error:", e)
