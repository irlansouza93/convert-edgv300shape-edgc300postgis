# 💻 WIKI DO PROJETO: Guia Avançado (Desenvolvedores e Arquitetos)

Este guia destina-se a Engenheiros de Software e Orquestradores de Dados focados em interagir e construir em cima do núcleo Python, expandindo os limites e mantendo o *Clean Code* inviolável do projeto.

---

## 1. Topologia e Arquitetura do Software (Hexagonal/SOLID)

O projeto `shp_to_postgis_converter` baseia-se na ideia de **Separação de Preocupações**, fortemente inspirado em **Ports and Adapters** e **Domain-Driven Design (DDD)**. 

### O Coração Intocável (`src/domain/`)
Aqui habitam as **Entity** e as regras de negócio puras (Aglomeradas na classe `MappingRules`).
O Domínio não tem nenhuma importação de Infra (`geopandas`, conexões IP de banco, escrita OS em disco ou bibliotecas web). Ele dita As Regras Abstratas de conversão (O "O que" Fazer).

### O Orquestrador Central (`src/application/`)
Encarne o `MapperService` (em especial a classe `GeometricAttributeMapper`) como o Caso de Uso principal do sistema. Este cara pergunta o que fazer para o Domínio e manda a Infraestrutura traduzi-lo. **Toda a auditoria global, logs de _Fallback_ e tradução de tipos fica fechada nessa classe**, tornando o sistema puramente testável em memória.

### Os Conduites Periféricos (`src/infrastructure/`)
Aqui vivem as tecnologias voláteis. Os adaptadores:
* `shapefile_reader.py`: Usa Geopandas, que não trafega nada em memória RAM bruta de forma pesada, graças a sintaxe *Generator* `yield`.
* `sql_writer.py`: Orquestra comandos textuais para o Postgres.

Se no futuro a conexão Mudar (Ex: de Disco C: para Banco de Dados na AWS via TCP), tudo recairá sob criar um novo script em `.infrastructure` (como `remote_postgis_reader.py`), preservando todas as demais pastas sem refatoramentos de espaguete. `main.py` atuará apenas delegando a Inversão de Controle (IoC).

---

## 2. Paradigmas Reativos de Machine Learning 

### A Semente Inicial e Expansão por Machine Learning
O sistema nunca assume e desiste que algo não pode ser mapeado se o masterfile JSON (A "cartilha") possuir ausências ou sub-classes não previstas pela modelagem FME prévia. Contamos com um sistema à parte construído na raiz de scripts sob o arquivo `scripts/expand_conversao_json.py`.
Este Módulo utiliza lógicas computacionais leves:
1. **Verificação de Conjuntos:** Isola Tabelas Faltantes.
2. **Similaridade:** Emprega varredura via Prefixo ou difusão semântica (Fuzzy Matching *difflib*) num Threshold de corte de 0.6 sobre os Dicionários Master EDGV (*Master Shape e Master PostGIS*) pra interconectar geometrias e suas sub-colunas que foram desenhadas em séculos diferentes.
3. **Imutabilidade:** As execuções iterativas nunca engolem o JSON base. Ele sempre gera um espelho de *Rollback* como versão `_old.json` visando *Safety Pipeline Deployment*.

Uma vez concluído o processamento Fuzzy de expansão, os binários JSON passam pelo compilador vital `generate_mapping.py`, que constrói dezenas de `config/mapping_shp_to_pg.json` ultraleves baseando-se em O(1) Complexidade de busca por Dicionários Hash Python, sendo devorados milissegundo a milissegundo no `main.py`.

---

## 3. Ecossistema, Estilo e Testes

*   **Padrão Estilo:** PEP-8, variáveis e métodos globais auto-descritivos (Clean Code) 100% em Inglês. Mensagens GUI focadas na experiência do usuário de operação estritamente em português brasileiro (Ex: Warnings, Logs no terminal, CSV e Arquivos Fiscais Markdown).
*   **Test-Driven:** Cobertura de dependências nativa de Python pelo pacote `pytest`.
    Existem dois test-cases críticos integrados como faróis operacionais (`tests/test_converter.py` que testa Mock-Ups abstratas em *Memory Fake* e o gigantesco `test_completude_json.py`, atuando como Robô Fiscal auditando os Dicionários-Fonte para expor matematicamente se alguma feature ou tabela do dicionário EDGV 3.0 sumiu e desestruturou do escopo da compilação).
    Para validar Pull-Requests, exija na pipeline o passe de:
    `python -m pytest tests/ -v`.
