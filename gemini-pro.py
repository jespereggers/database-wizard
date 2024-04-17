import requests
import json

# API-Schlüssel und URL setzen
api_key = "YOUR_API_KEY"  # Ersetzen Sie dies durch Ihren API-Schlüssel
url = "https://vertex.ai/v1/models/{model_id}/predict"  # URL der API

# Prompt definieren
prompt = "Schreiben Sie ein Gedicht über die Schönheit der Natur."

# Anfrage erstellen
payload = {
    "inputs": {"text": prompt},
}
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
}

# Anfrage senden und Antwort empfangen
response = requests.post(url, json=payload, headers=headers)
response.raise_for_status()

# Antwort in JSON-Format parsen
response_json = json.loads(response.text)

# Ausgabe der Antwort
print(json.dumps(response_json, indent=4))
