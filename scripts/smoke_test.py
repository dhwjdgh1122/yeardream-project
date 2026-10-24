import json

import httpx

response = httpx.post(
    "http://127.0.0.1:8000/api/analyze",
    json={"url": "https://example.com"},
    timeout=20,
)

print("STATUS", response.status_code)
print(response.text)
