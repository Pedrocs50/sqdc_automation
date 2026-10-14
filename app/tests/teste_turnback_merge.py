from io import BytesIO
from pathlib import Path
import pandas as pd

from app.graph_client import GraphClient
from app.config import GRAPH_CONFIG
from app.oracle_client import get_connection


BASE_DIR = Path(__file__).resolve().parent.parent.parent
SQL_DIR = BASE_DIR / "sql"


def load_sql_file(file_name: str) -> str:
    sql_path = SQL_DIR / file_name
    return sql_path.read_text(encoding="utf-8")


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


def load_turnback_events() -> pd.DataFrame:
    client = GraphClient()
    client.acquire_token()

    file_id = GRAPH_CONFIG["file_ids"]["turnback"]
    url = f"https://graph.microsoft.com/v1.0/sites/{client.site_id}/drive/items/{file_id}/content"

    response = client.session.get(url, timeout=60)
    response.raise_for_status()

    file_bytes = BytesIO(response.content)

    df = pd.read_excel(file_bytes, sheet_name="2026 Atual")
    df = df[["Nota QM", "Data", "Desc CT Atual"]].copy()

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["CR"] = df["Desc CT Atual"].apply(map_cr)

    iso = df["Data"].dt.isocalendar()
    df["Ano"] = iso.year
    df["SemanaISO"] = iso.week

    df = df.dropna(subset=["Nota QM", "Data"])

    df_eventos = (
        df.groupby(["CR", "Ano", "SemanaISO"])["Nota QM"]
        .nunique()
        .reset_index(name="Eventos")
        .sort_values(["Ano", "SemanaISO", "CR"])
    )

    return df_eventos


def load_horas_confirmadas() -> pd.DataFrame:
    conn = get_connection()
    try:
        query = load_sql_file("horas_confirmadas_turnback.sql")
        df = pd.read_sql(query, conn)
        return df
    finally:
        conn.close()


def main():
    df_eventos = load_turnback_events()
    df_horas = load_horas_confirmadas()
    df_horas.columns = [col.upper() for col in df_horas.columns]

    df_horas = df_horas.rename(columns={
        "ANO": "Ano",
        "SEMANAISO": "SemanaISO",
        "HORASCONFIRMADAS": "HorasConfirmadas"
    })

    print("\nEVENTOS (SharePoint):")
    print(df_eventos.head(10))

    print("\nHORAS CONFIRMADAS (Oracle):")
    print(df_horas.head(10))

    df_final = df_eventos.merge(
        df_horas,
        on=["CR", "Ano", "SemanaISO"],
        how="inner"
    )

    df_final["Turnback"] = (
        df_final["Eventos"] / df_final["HorasConfirmadas"]
    ) * 1_000_000

    print("\nMERGE FINAL:")
    print(df_final.head(20))


if __name__ == "__main__":
    main()
