# Revisão Arquitetural - SQDC Automation

## 1. Resumo do documento analisado

O documento `SQDC_Requisitos_Arquitetura (1).docx` descreve o sistema como um MVP de ETL para métricas SQDC com foco em:

- Coleta automatizada de dados de IUH/Hora Catraca via One Cockpit.
- Processamento e cálculo de métricas SQDC.
- Armazenamento em nuvem via Microsoft Graph API / SharePoint.
- Geração de relatórios consolidados por área e semana.
- Suporte inicial para Fuselagem e Pintura.

O roadmap futuro inclui dashboard web, integração SAP, configuração self-service e alertas/analítica histórica.

## 2. Avaliação da arquitetura atual proposta pelo documento

O documento propõe uma arquitetura em camadas com um pipeline ETL: Extract -> Transform -> Load. Isso é uma boa direção para o MVP. No entanto, o projeto atual não implementa a separação de responsabilidades com clareza, e mistura:

- lógica de negócios com acesso a dados,
- transformação de métricas com transporte de APIs externas,
- validação de configuração com importação direta de módulos.

### Pontos positivos do documento

- Boa visão de domínio e escopo MVP claro.
- Uso correto do padrão ETL para o problema.
- Identificação de diferentes fontes: One Cockpit, OEE, SharePoint DPR, SAP.
- Reconhecimento de necessidade de configuração por área (YAML/JSON).

### Limites da proposta atual

- Arquitetura em camadas está bem, mas precisa ser amadurecida para Clean Architecture / Portas e Adaptadores.
- O documento fala em estrutura de diretórios e pipeline, mas o código atual não segue uma estrutura definida.
- Há dependência direta do domínio em infraestrutura, especialmente no módulo `app.indicators.turnback_gerencia`.

## 3. Principais problemas de organização e acoplamento no código atual

### 3.1 `app/main.py` está excessivamente acoplado

- Faz orquestração, acesso a banco, leitura de SQL, transformação, salvamento JSON e publicação Graph em um único módulo.
- Usa importação direta de transformers específicos (`iuh_gerencia`, `turnback_gerencia`, etc.).
- Não há injeção de dependência: `GraphClient()` e `get_connection()` são instanciados diretamente.
- A configuração global `APP_CONFIG` e `GRAPH_CONFIG` é lida em tempo de importação, tornando testes e injeção difíceis.

### 3.2 `GraphClient` está violando SRP e acoplando regras de negócio

- Além de autenticar e chamar Graph API, ele contém mapeamento de campos por lista.
- Possui validação de configuração e montagem de payloads de negócio.
- Deve ser responsabilidade de um adaptador/infrastructure-only client, não de uma classe de domínio.

### 3.3 `Turnback` mistura camadas

- `turnback_gerencia.py` acessa SharePoint via `GraphClient`, Oracle via `get_connection`, faz SQL, processa Excel e calcula métricas.
- Essa unidade faz extração, transformação e infraestrutura ao mesmo tempo.
- O módulo não garante separação entre domínio, aplicação e infraestrutura.

### 3.4 `config.py` é global e com efeito colateral na importação

- A carga de variáveis de ambiente é feita no módulo e falha imediatamente se estiver incompleta.
- Isso dificulta testes unitários e composição do aplicativo.
- Recomendação: separar carregamento de configuração, validação e acesso às variáveis.

### 3.5 Falta de abstrações e interfaces

- Não existe interface para origem de dados, para publicador de resultados ou para cliente Graph.
- O uso direto de `msal`, `requests`, `pandas`, `oracledb` e `GraphClient` em camadas superiores quebra o princípio de inversão de dependência.

### 3.6 Estrutura de testes fraturada

- Os testes estão dentro de `app/tests/` e usam nomes `teste_*` em vez de `test_*`.
- Não há separação clara entre testes unitários, de integração e de mocks.
- O nome de arquivo `teste_graph_ids.py` indica mais script exploratório do que suíte de teste.

## 4. Estrutura de pastas ideal para o MVP e evolução futura

### 4.1 Recomendações gerais

- Mantenha `app/` como package principal ou mova para `src/` se planejar empacotar.
- Separe claramente as camadas:
  - `domain/` - entidades, regras de negócio e serviços de domínio.
  - `application/` - casos de uso, orquestração e DTOs.
  - `infrastructure/` - adaptadores de dados externos, Graph, Oracle, arquivos.
  - `presentation/` - CLI, script de execução, eventual API/serviço web.
- Use `shared/` ou `common/` para utilitários genéricos e constantes, não para lógica de domínio.
- Armazene configuração de área/indicador em YAML/JSON separada de código.

### 4.2 Estrutura sugerida

```text
app/
├── __init__.py
├── main.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── env.py
│   └── area_config.py
├── domain/
│   ├── models/
│   │   ├── area.py
│   │   ├── indicator.py
│   │   ├── metric.py
│   │   ├── period.py
│   │   └── value_objects.py
│   ├── services/
│   │   ├── metric_calculator.py
│   │   └── turnback_calculator.py
│   ├── repositories/
│   │   ├── data_source.py
│   │   └── target_repository.py
│   └── exceptions.py
├── application/
│   ├── __init__.py
│   ├── use_cases/
│   │   ├── run_indicator.py
│   │   ├── publish_report.py
│   │   └── load_area_config.py
│   ├── dto/
│   │   ├── indicator_payload.py
│   │   └── metric_dto.py
│   └── pipeline/
│       ├── etl_pipeline.py
│       └── steps.py
├── infrastructure/
│   ├── __init__.py
│   ├── graph/
│   │   ├── graph_client.py
│   │   ├── graph_repository.py
│   │   └── mapper.py
│   ├── oracle/
│   │   ├── oracle_client.py
│   │   ├── oracle_repository.py
│   │   └── query_loader.py
│   ├── files/
│   │   ├── excel_loader.py
│   │   └── config_reader.py
│   ├── persistence/
│   │   ├── json_writer.py
│   │   └── sharepoint_writer.py
│   └── config/
│       └── yaml_loader.py
├── indicators/
│   ├── __init__.py
│   ├── base.py
│   ├── iuh/
│   │   ├── gerencia.py
│   │   ├── supervisao.py
│   │   └── mapping.py
│   ├── hora_extra/
│   │   ├── gerencia.py
│   │   └── supervisao.py
│   └── turnback/
│       ├── gerencia.py
│       └── mapping.py
├── config_data/
│   ├── metas.json
│   └── areas/
│       ├── fuselagem.yaml
│       └── pintura.yaml
└── tests/
    ├── unit/
    ├── integration/
    ├── mocks/
    └── fixtures/

sql/
├── iuh_gerencia.sql
├── iuh_supervisao.sql
├── hora_extra_gerencia.sql
├── hora_extra_supervisao.sql
├── horas_confirmadas_turnback.sql
└── tests/
```

### 4.3 Onde cada arquivo deve ficar

- `app/main.py`: apresentação / CLI. Recebe dependências via composição e dispara o caso de uso.
- `app/config/settings.py`: carregamento e validação de configuração com Pydantic ou similar.
- `app/config/area_config.py`: leitura de arquivos YAML por área, separando regras de negócio dos dados.
- `app/domain/models/`: entidades de negócio e value objects.
- `app/domain/services/`: regras de cálculo de métricas, validações e processamento de domínios como IUH e Turnback.
- `app/domain/repositories/`: portas/contratos para busca de dados e publicação dos resultados.
- `app/application/use_cases/`: casos de uso como `ProcessIndicatorUseCase` e `PublishIndicatorUseCase`.
- `app/application/pipeline/`: orquestração do ETL com etapas reutilizáveis.
- `app/infrastructure/graph/graph_client.py`: adaptador técnico para Microsoft Graph.
- `app/infrastructure/graph/graph_repository.py`: implementação da porta de publicação/consulta de listas.
- `app/infrastructure/oracle/oracle_repository.py`: implementação do acesso a Oracle.
- `app/infrastructure/files/excel_loader.py`: leitura de arquivos Excel/CSV e mapeamento genérico.
- `app/infrastructure/persistence/json_writer.py`: gravação de JSON para análise local.
- `app/indicators/`: regras específicas de cada indicador, preferencialmente pequenas classes ou funções de mapeamento.

## 5. Como aplicar SOLID na prática neste projeto

### Single Responsibility Principle (SRP)

- `GraphClient` deve ter só responsabilidade de comunicação com Graph API.
- A lógica de montagem de payloads deve ser movida para `infrastructure/graph/mapper.py` ou `application/dto`.
- Cada `indicator` deve ter um serviço de transformação e um serviço de extração, não um módulo que faça ambos.
- `main.py` deve apenas orquestrar o caso de uso e tratar entrada/saída.

### Open/Closed Principle (OCP)

- Em vez de `INDICATOR_CONFIG` com condicionais, use uma fábrica de indicadores ou registro dinâmico.
- Adicione novos indicadores criando novas classes/estratégias, não alterando `main.py`.
- Crie uma interface `IndicatorProcessor` e implemente classes para `IuhGerencia`, `HoraExtraGerencia`, `TurnbackGerencia`.

### Liskov Substitution Principle (LSP)

- Qualquer implementação de repositório deve aceitar os mesmos contratos de sua interface.
- Ex.: um `OracleRepository` deve ser substituível por um `MockRepository` em testes.

### Interface Segregation Principle (ISP)

- Separe `IConnector` de `IPublisher`.
- Crie pequenas interfaces:
  - `IDataExtractor` (extrai dados de uma fonte).
  - `IDataTransformer` (transforma DataFrame/dados de domínio).
  - `IDataLoader` (persiste/ publica resultados).

### Dependency Inversion Principle (DIP)

- Camadas superiores (`application/`) devem depender de abstrações em `domain/` ou `application/`, não de classes concretas em `infrastructure/`.
- Exemplo:
  - `ProcessIndicatorUseCase(data_extractor: IDataExtractor, transformer: IDataTransformer, publisher: IDataLoader)`
- Implemente DI manualmente com composição em `main.py`, ou use um container leve.

## 6. Componentes por camada

### Domain

- Entidades: `Indicator`, `Area`, `Metric`, `Period`, `Target`, `Event`.
- Value Objects: `CR`, `SemanaISO`, `DataRange`.
- Serviços de domínio: `IuhCalculator`, `TurnbackCalculator`, `OeeCalculator`.
- Repositórios/Portas: contratos para buscar dados e obter metas.

### Application

- Casos de uso: `ProcessIndicatorUseCase`, `PublishIndicatorUseCase`, `LoadAreaConfigurationUseCase`.
- DTOs: representações de payload para Microsoft Lists e relatórios.
- Pipeline ETL: orquestração genérica de `extract -> transform -> load`.

### Infrastructure

- Graph API client e adaptador.
- Oracle client e repositório.
- File loaders (Excel, CSV, YAML).
- JSON writer e eventual SharePoint writer.
- Implementações de interfaces de persistência e extração.

### Presentation

- `app/main.py` CLI.
- Futuro: `app/presentation/web_api.py` ou `app/presentation/dashboard.py`.
- Scripts de execução e bootstrapping.

## 7. Design patterns adequados

- Strategy: para implementar diferentes abordagens de transformação por indicador.
- Template Method / Pipeline: para o fluxo ETL comum.
- Repository: para encapsular acesso a Oracle, SharePoint e Graph.
- Adapter: para integrar Microsoft Graph, Oracle e leitura de arquivos.
- Factory: para criar indicadores e pipelines configurados por área.
- Builder: para montar payloads complexos de publicação.
- Command/Use Case: para separação de ações de negócio.

## 8. Organização de testes

### Estrutura recomendada

```text
app/tests/
├── unit/
│   ├── domain/
│   ├── application/
│   ├── infrastructure/
│   └── indicators/
├── integration/
│   ├── etl_pipeline_test.py
│   ├── oracle_adapter_test.py
│   └── graph_adapter_test.py
├── mocks/
│   ├── graph_client_mock.py
│   ├── oracle_client_mock.py
│   └── excel_mock.py
└── fixtures/
    ├── sample_iuh.csv
    ├── sample_turnback.xlsx
    └── area_config.yaml
```

### Tipo de testes

- Unitários:
  - cálculos de IUH/TURBACK.
  - transformações de DataFrame.
  - validação de configuração.
  - mapeamentos de payload e campos.
- Integração:
  - conexão Oracle + leitura SQL + transformação.
  - leitura SharePoint/Excel + cálculo + JSON local.
  - fluxo completo de ETL com adaptadores reais ou stubs.
- Mocks:
  - `GraphClient` mockado para `publish` e `download file`.
  - `OracleRepository` mockado para dados de teste.
  - `FileLoader` mockado para Excel/YAML.

### Convenções de nomenclatura

- Arquivos de teste: `test_<module>.py`.
- Classes: `PascalCase`.
- Funções / variáveis: `snake_case`.
- Constantes: `UPPER_SNAKE_CASE`.
- Módulos: `snake_case`, por área ou responsabilidade.
- Keep `indicador` em português nos nomes de domínio apenas quando fizer sentido ao negócio; internamente prefira `indicator`, `metric`, `area`.

## 9. Riscos arquiteturais e melhorias

### Riscos atuais

- Alto acoplamento entre domínio e infraestrutura.
- `GraphClient` monolítico com lógica de negócio embutida.
- `main.py` difícil de testar e de estender.
- Configuração global em import-time impede composição controlada.
- Falta de validação e isolamento de contratos entre camadas.
- Implementação atual depende muito de `pandas` no núcleo, o que dificulta testes unitários finos se não estiver isolado.
- Não há versionamento de esquema de payload de list items para Graph.
- Mapeamento de campos e IDs fixos no código impede suporte a novas áreas sem deploy.

### Melhorias prioritárias

1. Extrair contratos (interfaces) para fontes de dados e publicadores.
2. Mover validação e leitura de .env para um `settings.py` com Pydantic.
3. Separar `extract`, `transform`, `load` em classes/funções independentes.
4. Criar adaptadores para Graph e Oracle. Não importe `requests` ou `oracledb` em `domain`.
5. Introduzir configuração por área (YAML) e separar metas de código.
6. Reorganizar testes em `unit/`, `integration/` e `mocks/`.
7. Adotar nomes de arquivos padrão de teste e converter `teste_*` para `test_*`.

## 10. Conclusão e recomendação

A arquitetura atual tem uma boa direção de domínio, mas precisa ser endurecida para ser escalável e profissional.

Para o MVP, priorize:

- um `application` layer leve que execute o pipeline;
- uma `infrastructure` layer com adaptadores puros;
- `domain` modelando métricas e regras de cálculo;
- `presentation` apenas como orquestrador/CLI.

Essa mudança mantém a simplicidade do MVP e abre espaço para as extensões futuras previstas pelo documento: dashboard, SAP, OEE, SharePoint e múltiplas áreas.

---

Arquivo gerado em `docs/architecture_review.md`.
