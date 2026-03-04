# Guia de Evolução e Migração para Novas Versões da EDGV

Este documento detalha as etapas arquiteturais e operacionais necessárias para adaptar o conversor atual para um novo cenário avançado: realizar a migração de dados de um banco PostGIS estruturado em uma versão antiga da EDGV (ex: EDGV 3.0 1.1.6) para um banco PostGIS com uma versão mais recente (ex: EDGV 3.0 Topo 1.4.5).

---

## 01. Como fazer a transição usando um JSON Incompleto e as novas Master Files?

O processo de migração de conhecimento neste caso se aproveita imensamente da Inteligência e da modularidade que já construímos. O passo a passo exato seria:

### Passo 1: Atualização da Matéria-Prima (Master Files)
Você deve ir até a pasta `source-knowledge/edgv-3-shapefile/` e trocar os arquivos fundamentais:
* **Antigo Shapefile Master vira o Banco Origem:** O arquivo que hoje é o `master_file_300_shp.json` deve ser substituído pelo Master File da versão PostGIS de origem (EDGV 3.0 1.1.6). O sistema o enxergará como a nova "Fonte" dos dados.
* **Antigo PostGIS Master vira o Banco Destino:** O arquivo `master_file_300.json` deve ser substituído pelo Master File da nova versão (EDGV Topo 1.4.5). O sistema o enxergará como o novo "Alvo".

### Passo 2: Injetando o JSON Incompleto
Pegue o seu JSON de conversão incompleto (da outra versão existente) e coloque-o na pasta `source-knowledge` com o nome de `conversao_pg-edgv-300_shp-edgv-300_completo.json`. Ele servirá como a "semente básica" de conhecimento.

### Passo 3: Expansão Autônoma da Inteligência
Abra o terminal e execute o utilitário que criamos:
`python scripts/expand_conversao_json.py`
Nós construímos essa ferramenta de forma genérica de propósito! Ela irá ler a nova estrutura Topo 1.4.5 (Alvo) e a estrutura 1.1.6 (Fonte). Tudo o que não estiver no seu JSON incompleto, a Inteligência Artificial fará a ponte automaticamente (prefixos e similaridade fuzzy) gerando as dezenas de tabelas restantes sem depender de programação rígida.

### Passo 4: Compilação do Motor
Rode `python scripts/generate_mapping.py`. O sistema filtrará esse Cérebro gigante que foi expandido pela IA e criará o arquivo levinho `config/mapping_shp_to_pg.json` para ser usado na conversão rápida.

### Passo 5: Adaptação de Código (O Novo Leitor)
Esta é a única etapa onde um código precisará ser feito, graças ao *Clean Architecture* (Regra SOLID da Inversão de Dependências).
Hoje, temos o `src/infrastructure/shapefile_reader.py`. Você precisará pedir a um engenheiro (ou criar) um `src/infrastructure/postgis_reader.py` (ou `geopackage_reader.py`). As camadas de Domínio (Regras) e Aplicação (`mapper_service.py`) **continuarão exatamente iguais e intactas**, elas não saberão que a fonte mudou. Apenas o "Adaptador" de origem será plugado no `main.py`.

---

## 02. No caso de conversão PostGIS para PostGIS, o que substitui a pasta de "Shapefiles Populados"?

Quando migramos os dados de PostGIS (Banco de Dados) para PostGIS (Banco de Dados), não estamos mais lidando com o limitador mundo de um diretório cheio de arquivos dejetos espalhados (como `.shp`, `.shx`, `.dbf`).

O que substituirá a pasta de entrada (`banco-edgv-3-sahpefile-populado`) será uma das duas opções abaixo, dependendo de como a sua rede de segurança militar/governamental opera:

### Opção A: Acesso Direto Remoto (Recomendado)
A "pasta de entrada" deixará de existir fisicamente no disco. O que você terá é um arquivo leve de configuração, como um `.env` ou `database.ini`, contendo as chaves de acesso:
```ini
host=192.168.1.50
port=5432
database=edgv_1_1_6_producao
user=usuario
password=senha
```
No `main.py`, substituiremos o "Buscar arquivos na pasta" por "Conectar ao Banco de Origem". O nosso script vai executar um `SELECT * FROM tabela_X` usando a memória RAM, aplicar as regras do `mapper_service.py` e cuspir tudo via nosso atual `output_edgv.sql`.

Esta abordagem é **100% viável e a mais recomendada arquiteturalmente**. Graças ao nosso design (*Clean Architecture/SOLID*), toda a inteligência do projeto está no `mapper_service.py` (Camada de Aplicação). As regras de negócio "não sabem" se a geometria veio de um arquivo ou da rede local TCP/IP; elas só pedem linhas de dados.

Para implementar isso na prática, qualquer desenvolvedor precisará apenas seguir estas duas etapas simples (*Plug and Play*):

**1. Criar o arquivo `src/infrastructure/postgis_reader.py`:**
Este adaptador se conectará à rede e ejetará linha por linha sem travar a RAM (Generator).
```python
import psycopg2
from src.domain.entities import ShapefileRecord # Podemos manter o nome ou renomear a entidade
from typing import Generator

class PostgisRemoteReader:
    def __init__(self, dsn: str):
        # Exemplo DSN: "dbname='edgv_old' user='postgres' host='192.168.1.50' password='123'"
        self.conn = psycopg2.connect(dsn)

    def get_tables(self) -> list:
        # Consulta ao banco para listar chaves (Ex: retorna ['aer_pista', 'ferrovia_l'...])
        return ["tabela_1", "tabela_2"]

    def read_records(self, table_name: str) -> Generator[ShapefileRecord, None, None]:
        with self.conn.cursor() as cur:
            # Comando SQL lendo tudo do banco velho
            cur.execute(f"SELECT *, ST_AsText(geom) as geom_wkt FROM {table_name}")
            columns = [desc[0] for desc in cur.description]
            
            for row in cur:
                row_dict = dict(zip(columns, row))
                geom_wkt = row_dict.pop('geom_wkt', None)
                yield ShapefileRecord(wkt_geometry=geom_wkt, attributes=row_dict)
```

**2. Plugar no `main.py` (Inversão de Dependências):**
No orquestrador `main.py`, substituiremos apenas a menção ao Shapefile por este novo leitor:
```python
# ANTES:
# from src.infrastructure.shapefile_reader import ShapefileReader
# reader = ShapefileReader(shp_input_dir)
# shapefiles = reader.get_shapefiles()

# DEPOIS:
from src.infrastructure.postgis_reader import PostgisRemoteReader
dsn = "dbname='edgv_old' user='postgres' host='192.168.1.50' password='123'"
reader = PostgisRemoteReader(dsn)
tabelas = reader.get_tables()

# E o resto do loop "for record in reader.read_records(tabela)" funciona igual!
```
Com apenas essas pequenas adições modulares, o resto da mágica do nosso `main.py` e do gerador de arquivo `.sql` funcionaria perfeitamente gerando os dados convertidos sem engasgar, consolidando a arquitetura escalável do projeto.
### Opção B: Banco em Arquivo Único Moderno (GeoPackage - GPKG)
Caso você ainda exija trabalhar de forma offline (passando os dados via pen-drive, por exemplo), o exército não precisa extrair "Shapefiles Múltiplos" do antigo banco PostGIS 1.1.6. Eles podem gerar um despejo em formato **GeoPackage (`.gpkg`)**. 
O GeoPackage é um moderno banco SQLite dentro de um único arquivo físico. Desta forma, a "pasta de entrada" conteria apenas **um único** arquivo chamado `edgv_estado_completo.gpkg`. O leitor do nosso projeto (usando o recém-adaptado geopandas nele) lerá todas as mais de 100 tabelas lá de dentro da base, dispensando a confusão de gerir milhares de shapefiles soltos na pasta.
