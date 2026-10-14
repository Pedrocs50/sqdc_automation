from io import BytesIO
import pandas as pd

from app.graph_client import GraphClient
from app.config import GRAPH_CONFIG


def map_cr(desc):
    if not isinstance(desc, str):
        return "Outros"

    txt = desc.strip().upper()

    if (
        "PRÉ PINTURA" in txt
        or "PRE PINTURA" in txt
        or "JUNÇÃO" in txt
        or "JUNCAO" in txt
    ):
        return "Junção"

    if "PINTURA" in txt:
        return "Pintura"

    return "Outros"


def main():
    client = GraphClient()
    client.acquire_token()

    file_id = GRAPH_CONFIG["file_ids"]["turnback"]

    url = f"https://graph.microsoft.com/v1.0/sites/{client.site_id}/drive/items/{file_id}/content"

    response = client.session.get(url, timeout=60)
    response.raise_for_status()

    file_bytes = BytesIO(response.content)

    df = pd.read_excel(file_bytes, sheet_name="2026 Atual")

    # Mantém só as colunas relevantes
    df = df[["Nota QM", "Data", "Desc CT Atual"]].copy()

    # Trata Data
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    # Cria CR
    df["CR"] = df["Desc CT Atual"].apply(map_cr)

    # Cria Ano e SemanaISO
    iso = df["Data"].dt.isocalendar()
    df["Ano"] = iso.year
    df["SemanaISO"] = iso.week

    # Remove linhas sem data / nota
    df = df.dropna(subset=["Nota QM", "Data"])

    # Agrega por CR / Ano / SemanaISO
    df_eventos = (
        df.groupby(["CR", "Ano", "SemanaISO"])["Nota QM"]
        .nunique()
        .reset_index(name="Eventos")
        .sort_values(["Ano", "SemanaISO", "CR"])
    )

    print("\nDADOS TRATADOS (primeiras linhas):\n")
    print(df.head())

    print("\nEVENTOS AGRUPADOS POR CR / ANO / SEMANAISO:\n")
    print(df_eventos.head(20))


if __name__ == "__main__":
    main()