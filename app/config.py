import os
from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Variável obrigatória não encontrada no .env: {name}")
    return value


ORACLE_CONFIG = {
    "user": require_env("ORACLE_USER"),
    "password": require_env("ORACLE_PASSWORD"),
    "host": require_env("ORACLE_HOST"),
    "port": int(os.getenv("ORACLE_PORT", 1521)),
    "service": require_env("ORACLE_SERVICE"),
    "client_lib_dir": os.getenv("ORACLE_CLIENT_LIB_DIR"),
}

APP_CONFIG = {
    "output_dir": os.getenv("OUTPUT_DIR", "output"),
    "log_level": os.getenv("LOG_LEVEL", "INFO").upper(),
}

GRAPH_CONFIG = {
    "tenant_id": require_env("GRAPH_TENANT_ID"),
    "client_id": require_env("GRAPH_CLIENT_ID"),
    "site_id": require_env("GRAPH_SITE_ID"),
    "site_url": os.getenv("GRAPH_SITE_URL"),
    "list_ids": {
        "iuh_gerencia": require_env("GRAPH_LIST_ID_IUH_GERENCIA"),
        "iuh_supervisao": require_env("GRAPH_LIST_ID_IUH_SUPERVISAO"),
        "hora_extra_gerencia": require_env("GRAPH_LIST_ID_HORA_EXTRA_GERENCIA"),
        "hora_extra_supervisao": require_env("GRAPH_LIST_ID_HORA_EXTRA_SUPERVISAO"),
        "turnback_gerencia": require_env("GRAPH_LIST_ID_TURNBACK_GERENCIA"),
    },
    "file_ids": {
        "turnback": require_env("GRAPH_FILE_ID_TURNBACK"),
    },
    "file_names": {
        "turnback": require_env("GRAPH_FILE_NAME_TURNBACK"),
    },
    "scopes": [
        scope.strip()
        for scope in os.getenv("GRAPH_SCOPES", "Sites.ReadWrite.All").split(",")
        if scope.strip()
    ],
}