import pytest
import os
import json
from src.domain.mapping_rules import MappingRules
from src.domain.entities import ShapefileRecord, PostGISRecord
from src.application.mapper_service import GeometricAttributeMapper
from src.infrastructure.sql_writer import SqlScriptWriter

# --- Fixtures ---
@pytest.fixture
def sample_mapping_file(tmp_path):
    """Cria um json de mapeamento falso para testes."""
    mapping_data = {
        "class_mapping": [
            {
                "shp_class": "AER_Pista_Ponto_Pouso",
                "pg_table": "aer_pista_ponto_pouso",
                "pg_class_def": "pista_ponto_pouso",
                "attributes": [
                    {
                        "shp_attr": "NOME",
                        "pg_attr": "nome",
                        "pg_type": "varchar(255)",
                        "is_domain": False
                    },
                    {
                        "shp_attr": "OPERACION",
                        "pg_attr": "operacional",
                        "pg_type": "smallint",
                        "is_domain": True,
                        "value_map": {
                            "Sim": 1,
                            "SIM": 1,
                            "Não": 0,
                            "NÃO": 0,
                            "Desconhecido": 99
                        }
                    }
                ]
            }
        ]
    }
    
    file_path = tmp_path / "test_mapping.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(mapping_data, f)
    
    return str(file_path)

# --- Testes de Domínio ---
def test_mapping_rules_loading(sample_mapping_file):
    rules = MappingRules(sample_mapping_file)
    assert rules.get_pg_table("AER_Pista_Ponto_Pouso") == "aer_pista_ponto_pouso"
    assert rules.get_pg_table("CLASSE_INEXISTENTE") is None

def test_mapper_service_with_domains(sample_mapping_file):
    rules = MappingRules(sample_mapping_file)
    mapper = GeometricAttributeMapper(rules)
    
    # Simula um registro lido do Shapefile
    shp_record = ShapefileRecord(
        wkt_geometry="LINESTRING (0 0, 1 1)",
        attributes={
            "NOME": "Aeroporto Municipal",
            "OPERACION": "Sim",
            "ID": 123 # Deveria ser ignorado
        }
    )
    
    pg_record = mapper.map_record("AER_Pista_Ponto_Pouso", "AER_Pista_Ponto_Pouso_A", shp_record)
    
    assert pg_record is not None
    assert pg_record.table_name == "aer_pista_ponto_pouso_a"
    assert pg_record.wkt_geometry == "LINESTRING (0 0, 1 1)"
    
    # Verifica traduções
    assert "nome" in pg_record.attributes
    assert pg_record.attributes["nome"] == "Aeroporto Municipal"
    
    # Verifica a tradução do domínio de String ("Sim") para Inteiro (1)
    assert "operacional" in pg_record.attributes
    assert pg_record.attributes["operacional"] == 1
    
    # Verifica se a PK "ID" foi devidamente ignorada para o banco gerenciar
    assert "id" not in pg_record.attributes

# --- Testes de Infraestrutura (Escrita SQL) ---
def test_sql_writer_formatting(tmp_path):
    out_file = tmp_path / "out.sql"
    writer = SqlScriptWriter(str(out_file), schema_name="edgv")
    
    records = [
        PostGISRecord(
            table_name="teste_tabela",
            wkt_geometry="POINT (10 20)",
            attributes={
                "nome": "O'Connor", # Teste de escape de aspas
                "operacional": 1,
                "nulo": None
            }
        )
    ]
    
    writer.write_inserts(records)
    writer.close()
    
    with open(out_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "BEGIN;" in content
    assert "COMMIT;" in content
    
    # Validando o texto gerado
    expected_insert = "INSERT INTO edgv.teste_tabela (nome, operacional, nulo, geom) VALUES ('O''Connor', 1, NULL, ST_GeomFromText('POINT (10 20)', 4674));"
    assert expected_insert in content
