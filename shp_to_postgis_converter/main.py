import os
import sys

# Adiciona diretório pai ao PYTHONPATH para imports do src funcionarem ao rodar arquivo
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.domain.mapping_rules import MappingRules
from src.infrastructure.shapefile_reader import ShapefileReader
from src.infrastructure.sql_writer import SqlScriptWriter
from src.application.mapper_service import GeometricAttributeMapper

def main():
    base_dir = r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme"
    shp_input_dir = os.path.join(base_dir, "source-knowlegde", "banco-edgv-3-sahpefile-populado")
    mapping_filepath = os.path.join(base_dir, "shp_to_postgis_converter", "config", "mapping_shp_to_pg.json")
    output_filepath = os.path.join(base_dir, "shp_to_postgis_converter", "output_edgv.sql")

    print("Carregando regras de mapeamento do JSON...")
    
    if not os.path.exists(mapping_filepath):
        print(f"ERRO: Arquivo de mapeamento '{mapping_filepath}' não encontrado.")
        print("Execute o script 'generate_mapping.py' antes de rodar a conversão.")
        sys.exit(1)
        
    mapping_rules = MappingRules(mapping_filepath)
    mapper = GeometricAttributeMapper(mapping_rules)
    
    print(f"Buscando arquivos shapefile em '{shp_input_dir}'...")
    reader = ShapefileReader(shp_input_dir)
    shapefiles = reader.get_shapefiles()
    
    if not shapefiles:
        print("Nenhum arquivo .shp encontrado no diretório!")
        sys.exit(1)

    print(f"Foram encontrados {len(shapefiles)} shapefiles para processamento.")
    print("Iniciando a geração do SQL do PostGIS na pasta do conversor...\n")
    
    writer = SqlScriptWriter(output_filepath, schema_name="edgv")
    
    total_processed = 0
    total_errors = 0
    
    audit_file = "relatorio_inconsistencias.csv"
    if os.path.exists(audit_file):
        os.remove(audit_file)
    
    # Processa arquivo por arquivo
    for shp_file in shapefiles:
        filename = os.path.basename(shp_file)
        
        # O Nome da classe no Shapefile é o nome do arquivo sem a extensão
        # Ex: "AER_Pista_Ponto_Pouso_A"
        shp_class_name, _ = os.path.splitext(filename)
        
        print(f"Lendo e traduzindo: {shp_class_name}")
        
        # O mapper varre o generator
        try:
            records_lidos = reader.read_records(shp_file)
            pg_records_lote = []
            
            for shape_rec in records_lidos:
                # O shapefile usa a letra solta no fim do nome do arquivo (ex: _A, _L, _P) 
                # O dicionário do master file espera na verdade que retiremos esse sufixo.
                # A chave gerada antes do '_A' é "AER_Pista_Ponto_Pouso"
                
                # Como extrair a classe real (excluindo os ultimos 2 caracteres '_A')
                real_class_name = shp_class_name[:-2] if shp_class_name[-2:] in ("_A", "_L", "_P") else shp_class_name
                
                pg_rec = mapper.map_record(real_class_name, shp_class_name, shape_rec)
                
                if pg_rec:
                    pg_records_lote.append(pg_rec)
                    total_processed += 1
            
            # Grava no disco as feições traduzidas em bloco
            if pg_records_lote:
                writer.write_inserts(pg_records_lote)
                
        except Exception as e:
            print(f"!! Falha ao converter feições do arquivo {filename}: {e}")
            total_errors += 1
            
    writer.close()
    
    print("\n------------------------------")
    print("CONVERSÃO CONCLUÍDA")
    print(f"Arquivo gerado: {output_filepath}")
    print(f"Total de registros mapeados com sucesso: {total_processed}")
    print(f"Total de arquivos com erro de leitura: {total_errors}")

if __name__ == "__main__":
    main()
