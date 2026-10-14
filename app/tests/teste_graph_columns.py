from app.graph_client import GraphClient


def main():
    client = GraphClient()
    client.acquire_token()

    list_key = "hora_extra_gerencia"
    list_id = client.get_list_id(list_key)

    url = f"https://graph.microsoft.com/v1.0/sites/{client.site_id}/lists/{list_id}/columns"
    response = client.session.get(url, timeout=30)

    if not response.ok:
        raise RuntimeError(
            f"Erro ao buscar colunas da list: {response.status_code} - {response.text}"
        )

    data = response.json()

    print("\nCOLUNAS DA LIST:\n")

    for col in data.get("value", []):
        print(
            f"DisplayName: {col.get('displayName')} | "
            f"Name(interno): {col.get('name')} | "
            f"ID: {col.get('id')}"
        )


if __name__ == "__main__":
    main()