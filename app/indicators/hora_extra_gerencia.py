from pathlib import Path
import json
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
METAS_FILE = BASE_DIR / "config_data" / "metas.json"


def get_meta_hora_extra_gerencia() -> float | None:
    if not METAS_FILE.exists():
        raise FileNotFoundError(f"Arquivo de metas não encontrado: {METAS_FILE}")

    with METAS_FILE.open("r", encoding="utf-8") as f:
        metas = json.load(f)

    return metas.get("hora_extra_gerencia", {}).get("default", {}).get("Meta")


def transform_hora_extra_gerencia(df: pd.DataFrame) -> list[dict]:
    """
    Transforma o resultado da query de Hora Extra Gerência em uma lista de dicionários
    pronta para envio futuro ao Microsoft Lists.
    """

    df = df.copy()

    # Padroniza nomes das colunas vindas do Oracle
    df.columns = [col.upper() for col in df.columns]

    # Renomeia para o padrão do projeto / Microsoft List
    column_mapping = {
        "TITLE": "Title",
        "ANO": "Ano",
        "SEMANAISO": "SemanaISO",
        "DATAINICIOSEMANA": "DataInicioSemana",
        "DATAFIMSEMANA": "DataFimSemana",
        "CR": "CR",
        "HORASEXTRAS": "HorasExtras",
        "HORASCATRACA": "HorasCatraca",
        "HORAEXTRAPERC": "HoraExtraPerc",
        "META": "Meta",
        "DATAATUALIZACAO": "DataAtualizacao",
        "FONTE": "Fonte",
    }

    df = df.rename(columns=column_mapping)
    
    if "HoraExtraPerc" in df.columns:
        df["HoraExtraPerc"] = df["HoraExtraPerc"] / 100

    # Normaliza Meta para decimal quando vier em percentual (5 -> 0.05)
    if "Meta" in df.columns:
        df["Meta"] = df["Meta"].apply(
            lambda x: x / 100 if pd.notnull(x) and x > 1 else x
        )
    else:
        df["Meta"] = get_meta_hora_extra_gerencia()

    # Converte datas para string ISO
    date_columns = ["DataInicioSemana", "DataFimSemana", "DataAtualizacao"]

    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: x.isoformat() if pd.notnull(x) and hasattr(x, "isoformat") else None
            )

    # Converte NaN para None
    df = df.where(pd.notnull(df), None)

    # Retorna lista de dicionários
    records = df.to_dict(orient="records")

    return records