## Comandos de execução

### Rodar IUH Gerência
python -m app.main --indicator iuh_gerencia

### Rodar IUH Gerência com debug
python -m app.main --indicator iuh_gerencia --debug

### Rodar IUH Gerência com debug e salvar JSON
python -m app.main --indicator iuh_gerencia --debug --save-json

### Rodar IUH Gerência e publicar na Microsoft List
python -m app.main --indicator iuh_gerencia --publish

### Rodar IUH Gerência com debug, salvar JSON e publicar
python -m app.main --indicator iuh_gerencia --debug --save-json --publish

### Rodar IUH Supervisão
python -m app.main --indicator iuh_supervisao

### Rodar IUH Supervisão com debug
python -m app.main --indicator iuh_supervisao --debug

### Rodar IUH Supervisão com debug e salvar JSON
python -m app.main --indicator iuh_supervisao --debug --save-json

### Rodar IUH Supervisão e publicar na Microsoft List
python -m app.main --indicator iuh_supervisao --publish

### Rodar IUH Supervisão com debug, salvar JSON e publicar
python -m app.main --indicator iuh_supervisao --debug --save-json --publish


### Rodar Hora Extra Gerência
python -m app.main --indicator hora_extra_gerencia

### Rodar Hora Extra Gerência com debug
python -m app.main --indicator hora_extra_gerencia --debug

### Rodar Hora Extra Gerência e salvar JSON
python -m app.main --indicator hora_extra_gerencia --save-json

### Rodar Hora Extra Gerência e publicar na Microsoft List
python -m app.main --indicator hora_extra_gerencia --publish

### Rodar Hora Extra Gerência (debug, salvar JSON e publicar)
python -m app.main --indicator hora_extra_gerencia --debug --save-json --publish

### Rodar Hora Extra Supervisão
python -m app.main --indicator hora_extra_supervisao

### Rodar Hora Extra Supervisão com debug
python -m app.main --indicator hora_extra_supervisao --debug

### Rodar Hora Extra Supervisão e salvar JSON
python -m app.main --indicator hora_extra_supervisao --save-json

### Rodar Hora Extra Supervisão e publicar na Microsoft List
python -m app.main --indicator hora_extra_supervisao --publish

### Rodar Hora Extra Supervisão (debug, salvar JSON e publicar)
python -m app.main --indicator hora_extra_supervisao --debug --save-json --publish

### Rodar Turnback Gerência
python -m app.main --indicator turnback_gerencia

### Rodar Turnback Gerência com debug
python -m app.main --indicator turnback_gerencia --debug

### Rodar Turnback Gerência e salvar JSON
python -m app.main --indicator turnback_gerencia --save-json

### Rodar Turnback Gerência e publicar na Microsoft List
python -m app.main --indicator turnback_gerencia --publish

### Rodar Turnback Gerência (debug, salvar JSON e publicar)
python -m app.main --indicator turnback_gerencia --debug --save-json --publish

### achar o id list
python -m app.tests.teste_graph_ids

app/
├── main.py
├── config.py
│
├── core/
│   ├── registry.py
│   └── pipeline.py
│
├── sources/
│   ├── oracle/
│   │   ├── client.py
│   │   └── queries/
│   ├── sap/
│   │   ├── client.py
│   │   └── extractors/
│   └── files/
│       └── reader.py
│
├── indicators/
│   ├── iuh/
│   │   ├── gerencia.py
│   │   ├── supervisao.py
│   │   └── sql/
│   └── shared/
│       └── helpers.py
│
├── publishers/
│   ├── graph_client.py
│   ├── list_publisher.py
│   └── json_publisher.py
│
├── config_data/
│   └── metas.json
│
└── tests/
