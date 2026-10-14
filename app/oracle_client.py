import oracledb
from app.config import ORACLE_CONFIG


def init_oracle_client_if_needed():
    client_lib_dir = ORACLE_CONFIG.get("client_lib_dir")

    if not client_lib_dir:
        return

    try:
        oracledb.init_oracle_client(lib_dir=client_lib_dir)
    except Exception as e:
        raise RuntimeError(
            f"Falha ao inicializar Oracle Client em '{client_lib_dir}'. "
            f"Verifique se o Instant Client está instalado corretamente."
        ) from e


def get_connection():
    dsn = f"{ORACLE_CONFIG['host']}:{ORACLE_CONFIG['port']}/{ORACLE_CONFIG['service']}"

    try:
        connection = oracledb.connect(
            user=ORACLE_CONFIG["user"],
            password=ORACLE_CONFIG["password"],
            dsn=dsn
        )
        return connection
    except Exception as e:
        raise RuntimeError(
            f"Falha ao conectar no Oracle usando DSN '{dsn}' com o usuário '{ORACLE_CONFIG['user']}'."
        ) from e


# Inicializa o client ao importar o módulo
init_oracle_client_if_needed()