from app.graph_client import GraphClient


def main():
    client = GraphClient()

    print("Iniciando autenticação no Microsoft Graph...")
    client.acquire_token_device_flow()
    print("Autenticação concluída com sucesso.")

    record = {
        "Title": "TESTE_GRAPH_IUH_2026_23",
        "Ano": 2026,
        "SemanaISO": 23,
        "DataInicioSemana": "2026-06-01T00:00:00",
        "DataFimSemana": "2026-06-07T00:00:00",
        "CR": "TESTE",
        "HorasConfirmadas": 100.0,
        "HorasCatraca": 120.0,
        "IUH": 83.33,
        "Meta": 88,
        "DataAtualizacao": "2026-06-15T08:00:00",
        "Fonte": "Teste GraphClient"
    }

    print("Criando item de teste na Microsoft List...")
    result = client.create_list_item(record)

    print("Item criado com sucesso.")
    print(result)


if __name__ == "__main__":
    main()