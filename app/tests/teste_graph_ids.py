from urllib.parse import urlparse
import os
import requests
import msal
from dotenv import load_dotenv
from app.config import GRAPH_CONFIG

load_dotenv()


def acquire_token():
    tenant_id = GRAPH_CONFIG["tenant_id"]
    client_id = GRAPH_CONFIG["client_id"]
    scopes = GRAPH_CONFIG["scopes"]

    authority = f"https://login.microsoftonline.com/{tenant_id}"

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=authority,
    )

    flow = app.initiate_device_flow(scopes=scopes)

    if "user_code" not in flow:
        raise RuntimeError(f"Falha ao iniciar device flow: {flow}")

    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(
            f"Falha ao obter token: {result.get('error_description', result)}"
        )

    return result["access_token"]


def get_site_id(token: str, site_url: str) -> str:
    parsed = urlparse(site_url)
    hostname = parsed.netloc
    relative_path = parsed.path

    url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:{relative_path}"

    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"Erro ao buscar site por path: {response.status_code} - {response.text}"
        )

    data = response.json()
    return data["id"]


def list_site_lists(token: str, site_id: str):
    url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/lists"

    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30
    )

    if not response.ok:
        raise RuntimeError(
            f"Erro ao listar lists do site: {response.status_code} - {response.text}"
        )

    return response.json().get("value", [])


def main():
    site_url = os.getenv("GRAPH_SITE_URL")

    if not site_url:
        raise ValueError("Preencha GRAPH_SITE_URL no .env antes de rodar este teste.")

    token = acquire_token()
    print("Token obtido com sucesso.")

    site_id = get_site_id(token, site_url)
    print(f"\nSITE ID:\n{site_id}\n")

    lists = list_site_lists(token, site_id)

    print("LISTS ENCONTRADAS NO SITE:")
    for item in lists:
        print(f"- Nome: {item.get('name')} | ID: {item.get('id')}")


if __name__ == "__main__":
    main()
