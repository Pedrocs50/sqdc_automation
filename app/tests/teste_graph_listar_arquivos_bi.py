from app.graph_client import GraphClient


def main():
    client = GraphClient()
    client.acquire_token()

    # Pasta dentro da biblioteca padrão do site
    # Link que você mandou indica algo como:
    # Shared Documents / Dados / Dados BI
    folder_path = "Dados/Dados BI"

    url = (
        f"https://graph.microsoft.com/v1.0/sites/{client.site_id}"
        f"/drive/root:/{folder_path}:/children"
    )

    response = client.session.get(url, timeout=30)

    if not response.ok:
        raise RuntimeError(
            f"Erro ao listar arquivos da pasta: {response.status_code} - {response.text}"
        )

    data = response.json()

    print("\nARQUIVOS ENCONTRADOS:\n")
    for item in data.get("value", []):
        print(
            f"Nome: {item.get('name')} | "
            f"ID: {item.get('id')} | "
            f"Tamanho: {item.get('size')}"
        )


if __name__ == "__main__":
    main()