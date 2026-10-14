from io import BytesIO
import pandas as pd

from app.graph_client import GraphClient
from app.config import GRAPH_CONFIG


def main():
    client = GraphClient()
    client.acquire_token()

    file_id = GRAPH_CONFIG["file_ids"]["turnback"]

    url = f"https://graph.microsoft.com/v1.0/sites/{client.site_id}/drive/items/{file_id}/content"

    response = client.session.get(url, timeout=60)
    response.raise_for_status()

    file_bytes = BytesIO(response.content)

    # Lê o Excel em memória
    excel_file = pd.ExcelFile(file_bytes)

    print("\nABAS ENCONTRADAS:")
    for sheet in excel_file.sheet_names:
        print(f"- {sheet}")

    # Lê a primeira aba só para inspeção inicial
    df = pd.read_excel(file_bytes)

    print("\nCOLUNAS ENCONTRADAS:")
    print(df.columns.tolist())

    print("\nPRIMEIRAS 5 LINHAS:")
    print(df.head())


if __name__ == "__main__":
    main()