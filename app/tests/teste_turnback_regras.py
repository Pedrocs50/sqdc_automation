from io import BytesIO
import pandas as pd
import re

from app.graph_client import GraphClient
from app.config import GRAPH_CONFIG


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def extract_number(value):
    if pd.isna(value):
        return None

    txt = str(value).strip().upper()

    match = re.search(r"(\d+)", txt)
    if match:
        return int(match.group(1))

    return None


def map_cr(desc):
    txt = normalize_text(desc)

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


def has_any(text, keywords):
    txt = normalize_text(text)
    return any(k in txt for k in keywords)


def aplicar_regras(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalizações básicas
    df["Aplic"] = df["Aplic"].apply(extract_number)
    df["SubAplic"] = df["SubAplic"].apply(extract_number)

    df["CR"] = df["Desc CT Atual"].apply(map_cr)

    df["Excluir"] = False
    df["MotivosExclusao"] = ""

    def marcar(mask, motivo):
        df.loc[mask, "Excluir"] = True
        df.loc[mask, "MotivosExclusao"] = df.loc[mask, "MotivosExclusao"].apply(
            lambda x: motivo if not x else f"{x}; {motivo}"
        )

    # =========================
    # REGRA 1 - Duplicadas
    # Aplic 2 e 13 com Doc.ref contendo CD ou NC
    # =========================
    mask_duplicadas = (
        df["Aplic"].isin([2, 13])
        & (
            df["Descrição Doc de referência"].fillna("").str.upper().str.contains("CD", na=False)
            | df["Descrição Doc de referência"].fillna("").str.upper().str.contains("NC", na=False)
        )
    )
    marcar(mask_duplicadas, "Duplicada")

    # =========================
    # REGRA 2.1 - Ferramental
    # Aplic 4, 5 e 11
    # OU Descrição item do grupo contendo FERRAMENTAL
    # =========================
    mask_ferramental = (
        df["Aplic"].isin([4, 5, 11])
        | df["Descrição item do grupo"].fillna("").str.upper().str.contains("FERRAMENTAL", na=False)
    )
    marcar(mask_ferramental, "NC não produto - Ferramental")

    # =========================
    # REGRA 2.2 - Efetividade / Revalidação / Obsoleto
    # Aplic 9
    # =========================
    mask_efetividade = df["Aplic"].isin([9])
    marcar(mask_efetividade, "NC não produto - Efetividade/Revalidação/Obsoleto")

    # =========================
    # REGRA 3 - Falta de material
    # pares (Aplic, SubAplic)
    # =========================
    pares_falta_material = {
        (1, 2),
        (2, 6),
        (3, 4),
        (10, 2),
        (10, 17),
        (12, 12),
        (13, 14),
        (15, 13),
        (17, 17),
    }

    mask_falta_material = df.apply(
        lambda row: (row["Aplic"], row["SubAplic"]) in pares_falta_material,
        axis=1
    )
    marcar(mask_falta_material, "Falta de material")

    # =========================
    # REGRA 5 - Programas em phase-out
    # Aplic 7 / SubAplic 7
    # =========================
    mask_phaseout = (df["Aplic"] == 7) & (df["SubAplic"] == 7)
    marcar(mask_phaseout, "Programas desativados / phase-out")

    # =========================
    # REGRA 7 - Canibalização
    # =========================
    keywords_canibal = [
        "CANNIBAL",
        "CANIBAL",
        "CANBLZ",
        "CNBLZ",
        "CANIB",
        "CANIBALIZATION",
        "CANIBALIZACAO",
        "CANIBALIZAÇÃO",
        "CAN-",
    ]

    mask_canibal = (
        ((df["Aplic"] == 2) & (df["SubAplic"] == 3))
        | ((df["Aplic"] == 3) & (df["SubAplic"] == 5))
        | df["Descrição do Problema"].fillna("").str.upper().apply(lambda x: has_any(x, keywords_canibal))
        | df["Descrição tipo defeito"].fillna("").str.upper().str.contains("CANIB", na=False)
    )
    marcar(mask_canibal, "Canibalização")

    # =========================
    # REGRA 8 - APLICS especiais
    # =========================
    aplics_especiais = [14, 20, 21, 23, 28, 30, 32, 33, 34, 36, 37]
    mask_aplic_especial = df["Aplic"].isin(aplics_especiais)
    marcar(mask_aplic_especial, "Aplic especial fora do processo produtivo")

    # =========================
    # REGRA 10 - CTAs de logística
    # Descrição item do grupo contém LOG ou PLAN
    # =========================
    mask_logistica = (
        df["Descrição item do grupo"].fillna("").str.upper().str.contains("LOG", na=False)
        | df["Descrição item do grupo"].fillna("").str.upper().str.contains("PLAN", na=False)
    )
    marcar(mask_logistica, "Logística / Planning")

    # =========================
    # REGRA 12 - Referentes a decisões de programas
    # Aplic 7 + Descrição item do grupo = Programa
    # =========================
    mask_programa = (
        (df["Aplic"] == 7)
        & df["Descrição item do grupo"].fillna("").str.upper().str.contains("PROGRAMAS", na=False)
    )
    marcar(mask_programa, "Decisão de programa")

    # =========================
    # REGRA - Notas CDs duplicadas no turnback
    # Aplic 7 e 18 + Doc.Ref = Nota CD
    # =========================
    mask_nota_cd_duplicada = (
        df["Aplic"].isin([7, 18])
        & df["Descrição Doc de referência"].fillna("").str.upper().str.contains("NOTA CD", na=False)
    )
    marcar(mask_nota_cd_duplicada, "Nota CD duplicada no turnback")

    return df


def main():
    client = GraphClient()
    client.acquire_token()

    file_id = GRAPH_CONFIG["file_ids"]["turnback"]
    url = f"https://graph.microsoft.com/v1.0/sites/{client.site_id}/drive/items/{file_id}/content"

    response = client.session.get(url, timeout=60)
    response.raise_for_status()

    file_bytes = BytesIO(response.content)

    df = pd.read_excel(file_bytes, sheet_name="2026 Atual")

    colunas_necessarias = [
        "Nota QM",
        "Data",
        "Aplic",
        "SubAplic",
        "Descrição Doc de referência",
        "Desc CT Atual",
        "Descrição tipo defeito",
        "Descrição do Problema",
        "Descrição item do grupo",
    ]

    df = df[colunas_necessarias].copy()

    # Trata Data e cria Ano / SemanaISO
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    iso = df["Data"].dt.isocalendar()
    df["Ano"] = iso.year
    df["SemanaISO"] = iso.week

    df_tratado = aplicar_regras(df)

    print("\nTOTAL DE REGISTROS:")
    print(len(df_tratado))

    print("\nTOTAL EXCLUÍDOS:")
    print(df_tratado["Excluir"].sum())

    print("\nRESUMO POR MOTIVO:")
    resumo = (
        df_tratado[df_tratado["Excluir"]]
        .assign(Motivo=df_tratado["MotivosExclusao"].str.split("; "))
        .explode("Motivo")
        .groupby("Motivo")
        .size()
        .reset_index(name="Qtd")
        .sort_values("Qtd", ascending=False)
    )
    print(resumo)

    print("\nEXEMPLOS EXCLUÍDOS:")
    print(
        df_tratado.loc[df_tratado["Excluir"], [
            "Nota QM",
            "Data",
            "Aplic",
            "SubAplic",
            "Desc CT Atual",
            "MotivosExclusao"
        ]].head(20)
    )

    print("\nRESUMO POR SEMANA:")
    resumo_semana = (
        df_tratado.groupby(["Ano", "SemanaISO"])
        .agg(
            TotalRegistros=("Nota QM", "count"),
            Excluidos=("Excluir", "sum")
        )
        .reset_index()
        .sort_values(["Ano", "SemanaISO"])
    )

    resumo_semana["Considerados"] = (
        resumo_semana["TotalRegistros"] - resumo_semana["Excluidos"]
    )

    print(resumo_semana)

    print("\nRESUMO POR SEMANA E CR:")
    resumo_semana_cr = (
        df_tratado.groupby(["Ano", "SemanaISO", "CR"])
        .agg(
            TotalRegistros=("Nota QM", "count"),
            Excluidos=("Excluir", "sum")
        )
        .reset_index()
        .sort_values(["Ano", "SemanaISO", "CR"])
    )

    resumo_semana_cr["Considerados"] = (
        resumo_semana_cr["TotalRegistros"] - resumo_semana_cr["Excluidos"]
    )

    print(resumo_semana_cr)

    print("\nRESUMO GERÊNCIA POR SEMANA:")
    resumo_gerencia = (
        resumo_semana_cr.groupby(["Ano", "SemanaISO"], as_index=False)["Considerados"]
        .sum()
        .rename(columns={"Considerados": "ConsideradosGerencia"})
        .sort_values(["Ano", "SemanaISO"])
    )

    print(resumo_gerencia)
    print("\nDETALHE DOS EXCLUÍDOS POR SEMANA:")

    semanas = (
        df_tratado.loc[df_tratado["Excluir"], ["Ano", "SemanaISO"]]
        .drop_duplicates()
        .sort_values(["Ano", "SemanaISO"])
    )

    for _, row in semanas.iterrows():
        ano = row["Ano"]
        semana = row["SemanaISO"]

        print("\n" + "=" * 80)
        print(f"ANO {ano} | SEMANA {semana}")
        print("=" * 80)

        df_semana = df_tratado[
            (df_tratado["Ano"] == ano)
            & (df_tratado["SemanaISO"] == semana)
            & (df_tratado["Excluir"])
        ].copy()

        print(f"Total excluídos na semana: {len(df_semana)}")

        if df_semana.empty:
            print("Nenhum excluído nesta semana.")
            continue

        print(
            df_semana[
                [
                    "Nota QM",
                    "Data",
                    "Aplic",
                    "SubAplic",
                    "Desc CT Atual",
                    "Descrição item do grupo",
                    "Descrição tipo defeito",
                    "Descrição do Problema",
                    "MotivosExclusao",
                ]
            ].sort_values("Data")
        )


if __name__ == "__main__":
    main()