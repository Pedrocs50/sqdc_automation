import msal
from app.config import GRAPH_CONFIG


def main():
    tenant_id = GRAPH_CONFIG["tenant_id"]
    client_id = GRAPH_CONFIG["client_id"]
    scopes = GRAPH_CONFIG["scopes"]

    missing = []
    if not tenant_id:
        missing.append("GRAPH_TENANT_ID")
    if not client_id:
        missing.append("GRAPH_CLIENT_ID")
    if not scopes:
        missing.append("GRAPH_SCOPES")

    if missing:
        raise ValueError(
            "As variáveis abaixo precisam estar preenchidas no .env para testar a autenticação:\n"
            + "\n".join(f"- {item}" for item in missing)
        )

    authority = f"https://login.microsoftonline.com/{tenant_id}"

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=authority,
    )

    flow = app.initiate_device_flow(scopes=scopes)

    if "user_code" not in flow:
        raise RuntimeError(
            f"Não foi possível iniciar o device flow. Resposta: {flow}"
        )

    print("\n=== AUTENTICAÇÃO MICROSOFT GRAPH ===")
    print(flow["message"])
    print("====================================\n")

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(
            f"Falha ao obter token do Graph: {result.get('error_description', result)}"
        )

    print("Autenticação concluída com sucesso.")
    print("Token obtido com sucesso.")
    print(f"Escopos usados: {scopes}")
    print(f"Expires in: {result.get('expires_in')} segundos")


if __name__ == "__main__":
    main()
