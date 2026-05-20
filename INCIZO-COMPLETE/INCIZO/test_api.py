import urllib.request
import json

# Paste your Gemini API key here between the quotes
API_KEY ="AIzaSyDrIiVbhsqrQkYQJwp0c2DKR-17aE256eE"

print("Testing Gemini API connection...")
print(f"Key starts with: {API_KEY[:8]}...")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

payload = {
    "contents": [{"parts": [{"text": "Say hello"}]}],
    "generationConfig": {"maxOutputTokens": 50}
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(
    url, data=data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode('utf-8'))
        text = result['candidates'][0]['content']['parts'][0]['text']
        print(f"\n✓ SUCCESS! Gemini responded: {text}")
        print("\nYour API key works! Now run hyro_ai_pro.py")
except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8')
    print(f"\n✗ HTTP Error {e.code}: {body}")
except Exception as e:
    print(f"\n✗ Error: {str(e)}")

input("\nPress Enter to close...")
