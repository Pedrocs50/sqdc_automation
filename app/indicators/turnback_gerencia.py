from io import BytesIO
from pathlib import Path
from datetime import datetime
import json
import pandas as pd

from app.graph_client import GraphClient
from app.config import GRAPH_CONFIG
from app.oracle_client import get_connection


APP_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = APP_DIR.parent
METAS_FILE = APP_DIR / "config_data" / "metas.json"
SQL_DIR = PROJECT_ROOT / "sql"


def load_sql_file(file_name: str) -> str:
    sql_path = SQL_DIR / file_name
    return sql_path.read_text(encoding="utf-8")


def get_meta_turnback_gerencia() -> float | None:
    if not METAS_FILE.exists():
        raise FileNotFoundError(f"Arquivo de metas não encontrado: {METAS_FILE}")

    with METAS_FILE.open("r", encoding="utf-8") as f:
        metas = json.load(f)

    return metas.get("turnback_gerencia", {}).get("default", {}).get("Meta")


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
    """
    Lê o arquivo TURNBACK do SharePoint em memória e devolve:
    CR | Ano | SemanaISO | Eventos
    """
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
    """
    Lê do Oracle e devolve:
    CR | Ano | SemanaISO | HorasConfirmadas
    """
    conn = get_connection()

    try:
        query = load_sql_file("horas_confirmadas_turnback.sql")
        df = pd.read_sql(query, conn)

        df.columns = [col.upper() for col in df.columns]
        df = df.rename(columns={
            "ANO": "Ano",
            "SEMANAISO": "SemanaISO",
            "HORASCONFIRMADAS": "HorasConfirmadas"
        })

        return df

    finally:
        conn.close()


def build_turnback_gerencia_dataframe() -> pd.DataFrame:
    """
    Monta o DataFrame final do Turnback Gerência já pronto para o transform.
    Resultado final:
    TITLE | ANO | SEMANAISO | DATAINICIOSEMANA | DATAFIMSEMANA | CR |
    EVENTOS | HORASCONFIRMADAS | TURNBACK | META | DATAATUALIZACAO | FONTE
    """
    df_eventos = load_turnback_events()
    df_horas = load_horas_confirmadas()

    # Junta no nível de CR / semana
    df_merge = df_eventos.merge(
        df_horas,
        on=["CR", "Ano", "SemanaISO"],
        how="inner"
    )

    # Consolida para GERÊNCIA (Junção + Pintura juntos por semana)
    df_final = (
        df_merge.groupby(["Ano", "SemanaISO"], as_index=False)[["Eventos", "HorasConfirmadas"]]
        .sum()
    )

    df_final = df_final.sort_values(["Ano", "SemanaISO"]).reset_index(drop=True)

    df_final["EventosAcumulados"] = df_final["Eventos"].cumsum()
    df_final["HorasConfirmadasAcumuladas"] = df_final["HorasConfirmadas"].cumsum()

    df_final["Turnback"] = (
        df_final["EventosAcumulados"] / df_final["HorasConfirmadasAcumuladas"]
    ) * 1_000_000

    df_final["Turnback"] = df_final["Turnback"].round(2)
    
    # Datas da semana ISO
    df_final["DataInicioSemana"] = pd.to_datetime(
        df_final["Ano"].astype(str)
        + "-W"
        + df_final["SemanaISO"].astype(str).str.zfill(2)
        + "-1",
        format="%G-W%V-%u",
        errors="coerce"
    )

    df_final["DataFimSemana"] = df_final["DataInicioSemana"] + pd.Timedelta(days=6)

    # Colunas de controle
    df_final["CR"] = "S079,S092"
    df_final["Meta"] = get_meta_turnback_gerencia()
    df_final["DataAtualizacao"] = datetime.now()
    df_final["Fonte"] = "SharePoint TURNBACK + Oracle ckf_spd_ordens"

    # Title
    df_final["Title"] = (
        df_final["Ano"].astype(str)
        + "_"
        + df_final["SemanaISO"].astype(str).str.zfill(2)
        + "_TURNBACK_GERENCIA"
    )

    # Ordem final com nomes no padrão esperado pelo transform
    df_final = df_final[
        [
            "Title",
            "Ano",
            "SemanaISO",
            "DataInicioSemana",
            "DataFimSemana",
            "CR",
            "Eventos",
            "HorasConfirmadas",
            "Turnback",
            "Meta",
            "DataAtualizacao",
            "Fonte",
        ]
    ].sort_values(["Ano", "SemanaISO"])

    return df_final


def transform_turnback_gerencia(df: pd.DataFrame) -> list[dict]:
    """
    Transforma o resultado final do Turnback Gerência em uma lista de dicionários
    pronta para envio ao Microsoft Lists.
    """

    df = df.copy()

    # Padroniza nomes das colunas
    df.columns = [col.upper() for col in df.columns]

    # Renomeia para o padrão do projeto
    column_mapping = {
        "TITLE": "Title",
        "ANO": "Ano",
        "SEMANAISO": "SemanaISO",
        "DATAINICIOSEMANA": "DataInicioSemana",
        "DATAFIMSEMANA": "DataFimSemana",
        "CR": "CR",
        "EVENTOS": "Eventos",
        "HORASCONFIRMADAS": "HorasConfirmadas",
        "TURNBACK": "Turnback",
        "META": "Meta",
        "DATAATUALIZACAO": "DataAtualizacao",
        "FONTE": "Fonte",
    }

    df = df.rename(columns=column_mapping)

    # Se o DataFrame não trouxer Meta, busca do metas.json
    if "Meta" not in df.columns:
        df["Meta"] = get_meta_turnback_gerencia()

    # Converte datas para string ISO
    date_columns = ["DataInicioSemana", "DataFimSemana", "DataAtualizacao"]

    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: x.isoformat() if pd.notnull(x) and hasattr(x, "isoformat") else None
            )

    # Converte NaN para None
    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")