import requests
from bs4 import BeautifulSoup

def get_link_content(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Stellt sicher, dass ein Fehler geworfen wird bei einem nicht erfolgreichen Statuscode
        soup = BeautifulSoup(response.text, 'html.parser')

        # Entferne Skripte und Stylesheets, da diese in der Regel nicht zum Hauptinhalt gehören
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Nutze get_text() um den Textinhalt ohne HTML-Tags zu erhalten
        text = soup.get_text()

        # Optional: Entferne mehrere aufeinanderfolgende Leerzeichen und Zeilenumbrüche
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    except requests.RequestException as e:
        return str(e)  # Gibt den Fehler als String zurück, falls einer auftritt
