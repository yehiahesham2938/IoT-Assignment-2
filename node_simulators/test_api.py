
import requests
import json

CHIRPSTACK_API_TOKEN = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjaGlycHN0YWNrIiwiaXNzIjoiY2hpcnBzdGFjayIsInN1YiI6ImY0MzgyNjc3LWJmODQtNDgxNS1iYzg3LTFlOTRjMThhZDlmYyIsInR5cCI6ImtleSJ9.i9pdRbhaDtycaOHzlwXDtdUfJAyiV50iTseohprhEBM'
URL = "http://localhost:8090/api/applications?limit=10"

headers = {
    'Authorization': f'Bearer {CHIRPSTACK_API_TOKEN}',
    'Content-Type': 'application/json'
}

resp = requests.get(URL, headers=headers)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text}")
