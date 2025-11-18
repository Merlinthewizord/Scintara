import json
import urllib.request

def chat(host="http://127.0.0.1", port=8000, prompt="Give me a one-sentence entry about neon rain."):
    url = f"{host}:{port}/v1/chat"
    body = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_new_tokens": 96,
        "temperature": 0.7,
        "top_p": 0.95
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["content"]

if __name__ == "__main__":
    print(chat())
