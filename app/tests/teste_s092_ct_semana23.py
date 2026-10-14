from pathlib import Path
import pandas as pd

from app.oracle_client import get_connection


BASE_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = BASE_DIR / "sql"


def load_sql_file(file_name: str) -> str:
    sql_path = SQL_DIR / file_name

    if not sql_path.exists():
        raise FileNotFoundError(f"Arquivo SQL não encontrado: {sql_path}")

    return sql_path.read_text(encoding="utf-8")


def main():
    conn = None

    try:
        conn = get_connection()
        print("Conexão com Oracle realizada com sucesso.")

        query = load_sql_file("teste_s092_ct_semana23.sql")
        df = pd.read_sql(query, conn)

        print("Resultado da query:")
        print(df)

    except Exception as e:
        print(f"Erro ao executar teste: {e}")

    finally:
        if conn is not None:
            conn.close()
            print("Conexão encerrada.")


if __name__ == "__main__":
    main()