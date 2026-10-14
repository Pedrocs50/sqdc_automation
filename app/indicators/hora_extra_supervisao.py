from pathlib import Path
import json
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
METAS_FILE = BASE_DIR / "config_data" / "metas.json"


def get_meta_hora_extra_supervisao(cr: str) -> float | None:
    if not METAS_FILE.exists():
        raise FileNotFoundError(f"Arquivo de metas não encontrado: {METAS_FILE}")

    with METAS_FILE.open("r", encoding="utf-8") as f:
        metas = json.load(f)

    return metas.get("hora_extra_supervisao", {}).get(cr, {}).get("Meta")


def transform_hora_extra_supervisao(df: pd.DataFrame) -> list[dict]:
    """
    Transforma o resultado da query de Hora Extra Supervisão em uma lista de dicionários
    pronta para envio ao Microsoft Lists.
    """

    df = df.copy()

    # Padroniza nomes das colunas vindas do Oracle
    df.columns = [col.upper() for col in df.columns]

    # Renomeia para o padrão do projeto
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
        "DATAATUALIZACAO": "DataAtualizacao",
        "FONTE": "Fonte",
    }

    df = df.rename(columns=column_mapping)

    if "HoraExtraPerc" in df.columns:
        df["HoraExtraPerc"] = df["HoraExtraPerc"] / 100


    # Adiciona Meta por CR
    df["Meta"] = df["CR"].apply(get_meta_hora_extra_supervisao)

    # Converte datas para string ISO
    date_columns = ["DataInicioSemana", "DataFimSemana", "DataAtualizacao"]

    for col in date_columns:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: x.isoformat() if pd.notnull(x) and hasattr(x, "isoformat") else None
            )

    # Converte NaN para None
    df = df.where(pd.notnull(df), None)

    records = df.to_dict(orient="records")
    return records
