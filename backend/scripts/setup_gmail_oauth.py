"""
Script de configuracion unica para Gmail API.

1. Ve a https://console.cloud.google.com/apis/credentials
2. Crea proyecto → "Gmail API" → Credentials → OAuth 2.0 Client ID
3. Tipo: "Desktop application", nombre: "Boleta SaaS"
4. Descarga el JSON como credentials.json y colocalo aqui
5. Ejecuta: python setup_gmail_oauth.py
6. Se abrira el navegador para autorizar
7. Al finalizar, se genera GMAIL_TOKEN_JSON (copia este valor a Railway)
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "gmail_token.json")


def main():
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"ERROR: No se encuentra {CREDENTIALS_FILE}")
        print("1. Ve a https://console.cloud.google.com/apis/credentials")
        print("2. Crea proyecto → habilita Gmail API")
        print("3. Credentials → Create Credentials → OAuth 2.0 Client ID")
        print("4. Application type: Desktop application")
        print("5. Descarga el JSON y guardalo como:", CREDENTIALS_FILE)
        return

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)

    token_data = json.loads(creds.to_json())
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

    print("\n" + "=" * 60)
    print("AUTORIZACION EXITOSA!")
    print("=" * 60)
    print(f"\nToken guardado en: {TOKEN_FILE}")
    print("\nCopia el siguiente JSON completo a Railway como GMAIL_TOKEN_JSON:\n")
    print(json.dumps(token_data))
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
