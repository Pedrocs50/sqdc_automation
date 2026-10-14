from pathlib import Path
import json
import argparse
import logging
import traceback
import pandas as pd

from app.oracle_client import get_connection
from app.config import APP_CONFIG
from app.indicators.iuh_gerencia import transform_iuh_gerencia
from app.indicators.iuh_supervisao import transform_iuh_supervisao
from app.indicators.hora_extra_gerencia import transform_hora_extra_gerencia
from app.indicators.hora_extra_supervisao import transform_hora_extra_supervisao
from app.indicators.turnback_gerencia import (
    build_turnback_gerencia_dataframe,
    transform_turnback_gerencia)
from app.graph_client import GraphClient


BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "sql"
OUTPUT_DIR = BASE_DIR / APP_CONFIG["output_dir"]


INDICATOR_CONFIG = {
    "iuh_gerencia": {
        "sql_file": "iuh_gerencia.sql",
        "transformer": transform_iuh_gerencia,
        "json_file": "iuh_gerencia.json",
        "list_key": "iuh_gerencia",
    },
    "iuh_supervisao": {
        "sql_file": "iuh_supervisao.sql",
        "transformer": transform_iuh_supervisao,
        "json_file": "iuh_supervisao.json",
        "list_key": "iuh_supervisao",
    },
    "hora_extra_gerencia": {
        "sql_file": "hora_extra_gerencia.sql",
        "transformer": transform_hora_extra_gerencia,
        "json_file": "hora_extra_gerencia.json",
        "list_key": "hora_extra_gerencia",
    },
    "hora_extra_supervisao": {
        "sql_file": "hora_extra_supervisao.sql",
        "transformer": transform_hora_extra_supervisao,
        "json_file": "hora_extra_supervisao.json",
        "list_key": "hora_extra_supervisao",
    },
    "turnback_gerencia": {
        "builder": build_turnback_gerencia_dataframe,
        "transformer": transform_turnback_gerencia,
        "json_file": "turnback_gerencia.json",
        "list_key": "turnback_gerencia",
},
}


def setup_logging(debug: bool = False):
    level = logging.DEBUG if debug else getattr(logging, APP_CONFIG["log_level"], logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )


def load_sql_file(file_name: str) -> str:
    sql_path = SQL_DIR / file_name

    if not sql_path.exists():
        raise FileNotFoundError(f"Arquivo SQL não encontrado: {sql_path}")

    return sql_path.read_text(encoding="utf-8")


def save_json_file(data: list, file_name: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_path = OUTPUT_DIR / file_name

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return output_path


def publish_records(records: list[dict], list_key: str, debug: bool = False):
    client = GraphClient()

    logging.info("Iniciando autenticação no Microsoft Graph...")
    client.acquire_token()
    logging.info("Autenticação no Microsoft Graph concluída com sucesso.")

    result = client.bulk_upsert_list_items(records, list_key)

    logging.info(
        "Publicação concluída. created=%s | updated=%s | skipped=%s | total=%s",
        result["created"],
        result["updated"],
        result["skipped"],
        result["total"]
    )

    if result["errors"]:
        for err in result["errors"]:
            logging.error("Falha no item %s: %s", err["Title"], err["error"])

def parse_args():
    parser = argparse.ArgumentParser(description="Executa a automação do SQDC.")
    parser.add_argument(
        "--indicator",
        choices=INDICATOR_CONFIG.keys(),
        default="iuh_gerencia",
        help="Define qual indicador será executado."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Exibe informações detalhadas e traceback completo em caso de erro."
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Salva o payload transformado em JSON na pasta de output."
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Publica os registros na Microsoft List correspondente ao indicador."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging(debug=args.debug)

    conn = None

    try:
        logging.info("Iniciando execução do SQDC Automation.")
        logging.info("Indicador selecionado: %s", args.indicator)

        indicator = INDICATOR_CONFIG[args.indicator]

        conn = get_connection()
        logging.info("Conexão com Oracle realizada com sucesso.")

        if "builder" in indicator:
            df = indicator["builder"]()
            logging.info("DataFrame montado com sucesso pelo builder do indicador.")
            logging.info("Total de linhas retornadas: %s", len(df))
        else:
            query = load_sql_file(indicator["sql_file"])
            logging.info("Arquivo SQL carregado com sucesso: %s", indicator["sql_file"])

            df = pd.read_sql(query, conn)
            logging.info("DataFrame carregado com sucesso.")
            logging.info("Total de linhas retornadas: %s", len(df))
            
        transformer = indicator["transformer"]
        records = transformer(df)

        logging.info("Transformação concluída.")
        logging.info("Total de registros prontos: %s", len(records))

        if records and args.debug:
            logging.debug("Primeiro registro transformado: %s", records[0])

        if args.save_json:
            output_path = save_json_file(records, indicator["json_file"])
            logging.info("Arquivo JSON salvo em: %s", output_path)
        else:
            logging.info("JSON não foi salvo.")

        if args.publish:
            publish_records(records, indicator["list_key"], debug=args.debug)
        else:
            logging.info("Publicação na Microsoft List não foi executada.")

        logging.info("Execução finalizada com sucesso.")

    except Exception as e:
        logging.error("Erro ao executar processo: %s", e)

        if args.debug:
            logging.error("Traceback completo:\n%s", traceback.format_exc())

    finally:
        if conn is not None:
            conn.close()
            logging.info("Conexão encerrada.")


if __name__ == "__main__":
    main()