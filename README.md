# EDGV 3.0: Shapefile to PostGIS Converter

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Sistema robusto, inteligente e escalável desenvolvido para automatizar a migração massiva de matrizes de dados geográficos (Shapefiles) para bancos de dados PostgreSQL/PostGIS, respeitando rigidamente as especificações da **EDGV 3.0 (Especificação Técnica para a Estruturação de Dados Geoespaciais Vetoriais)**.

O conversor implementa arquitetura orientada a domínio (Clean Architecture / *Ports and Adapters*) para isolar as lógicas de negócio dos processos de I/O, trazendo inteligência ao aplicar heurísticas avançadas de cruzamento semântico de dicionários e preenchimento de domínios controlados (*fallbacks*).

---

## 🎯 Arquitetura do Projeto
O motor foi modularizado segundo os princípios SOLID:
```text
mapeamento-fme/
├── docs/                       # Documentações estendidas (ex: SOP_Conversao) e logs
├── shp_to_postgis_converter/
│   ├── config/                 # Dicionários JSON gerados e consumidos pela Engine
│   ├── src/
│   │   ├── domain/             # Lógica central: Regras de Mapeamento e Entidades abstratas
│   │   ├── application/        # Caso de Uso (MapperService)
│   │   └── infrastructure/     # Adaptadores de entrada/saída (SQL, Shapefile via Geopandas)
│   ├── scripts/                # Geradores de dicionário offline
│   ├── tests/                  # Bateria de testes unitários (pytest)
│   ├── autofill_conversao.py   # AI Heurística que deduz correlações entre colunas desconhecidas
│   └── main.py                 # Orquestrador da Interface
└── source-knowlegde/           # Material bruto de pesquisa e os Master Files da EDGV
```

## 🚀 Como Funciona o Pipeline Funcional

O processo se divide em duas etapas principais que garantem a segurança do mapeamento:

### Fase 1: Inteligência e Mapeamento
* Ao rodar o `autofill_conversao.py`, a IA analisa o Master File do banco PostGIS e o Shapefile para criar um "Dicionário Semântico". Atributos corrompidos ou com nomes divergentes são reconciliados através de algoritmos matemáticos *fuzzy*, poupando o operador de associar as coisas uma-a-uma.
* O `scripts/generate_mapping.py` lê essa biblioteca semântica + as regras globais e **materializa** todas as traduções no arquivo final `config/mapping_shp_to_pg.json`.

### Fase 2: Execução de Batch 
* O orquestrador `main.py` lê a pasta de *source-knowledge/banco-edgv-3-sahpefile-populado*, instancia as classes de infraestrutura (GeoPandas) e o `MapperService` converte os domínios String para Int Codes oficiais da EDGV.
* As feições que porventura venham nulas/vazias do arquivo Shape sofrem fallbacks controlados (recebem código 9999 Seguro) para não quebrar a transação de Importação.
* O output é descarregado nativamente no script text `output_edgv.sql`.

---

## 💻 Instalação & Dependências

1. Instale as bibliotecas científicas de leitura local via `pip`:

```bash
cd shp_to_postgis_converter
pip install -r requirements.txt
```

2. Certifique-se de que os Shapefiles do projeto estão armazenados no caminho correto descrito pela pasta `source-knowlegde/banco-edgv-3-sahpefile-populado` e que os **Master Files JSON** do modelo EDGV 300 residem na pasta estática `source-knowlegde/edgv-3-shapefile/`.

---

## 🎮 Guia Prático de Execução

Se você estiver lidando com uma massa limpa e quiser gerar o SQL Final imediatamente:
```bash
python main.py
```

Se você precisou alterar uma tabela, ou percebeu que a coluna do seu novo shapefile mudou de nome e quer refazer o cruzamento semântico:
```bash
python autofill_conversao.py
python scripts/generate_mapping.py
python main.py
```

> **Verificação Contínua:** Após rodar o `main.py`, ele gerará (ou manterá vazio) o arquivo `relatorio_inconsistencias.csv`. Se houverem dados nesse arquivo, significa que colunas exigidas como NOT NULL `(1..1)` no PostGIS vieram vazias no Shapefile. O motor forçará a adoção do código **9999** (Seguro) lá, mas o csv permitirá que você descubra no QGIS quais geometrias estavam faltando informações.

Para saber mais sobre como corrigir nomes customizados, consulte o documento `/docs/SOP_Conversao.md`.

## 🛡️ Testes e Qualidade
Este projeto suporta testes contínuos para manter sua confiabilidade alta. Todos os testes podem ser disparados na pasta raiz usando o comando:

```bash
pytest tests/
```
