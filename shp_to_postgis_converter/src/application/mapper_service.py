import pandas as pd
import csv
import os
from typing import Optional
from src.domain.entities import ShapefileRecord, PostGISRecord
from src.domain.mapping_rules import MappingRules

class GeometricAttributeMapper:
    """
    Camada de Aplicação responsável por instanciar a regra correta 
    e traduzir ativamente os valores lidos do Shapefile para os 
    formatos esperados na tabela do banco PostGIS.
    """
    def __init__(self, mapping_rules: MappingRules):
        self.rules = mapping_rules

    def _transform_value(self, shp_val: any, mapping_info: dict) -> any:
        """
        Interpreta o mapeamento e aplica conversão se necessário (Ex: Domínio).
        """
        # Tratar tipos nulos antes
        if pd.isna(shp_val) or shp_val is None:
            if mapping_info and "default_value" in mapping_info:
                return mapping_info["default_value"]
            return None
            
        # Converter para int se no PostGIS for dominio e temos um map reverso pronto
        if mapping_info and mapping_info.get("is_domain"):
            val_map = mapping_info.get("value_map", {})
            val_str = str(shp_val).strip()
            
            # Tenta pegar exato
            if val_str in val_map:
                return val_map[val_str]
            # Tenta maiuscula e minuscula
            elif val_str.upper() in val_map:
                return val_map[val_str.upper()]
                
            # Fallback - se a string enviada pelo Shapefile nao mapear p/ nenhum id,
            # devolve o default code registrado no mapeamento (geralmente equivalente a "Desconhecido").
            return mapping_info.get("default_value")
            
        # Tratar conversão de Booleano (no SHP costuma vir TRUE/FALSE como string as vezes, ou 1/0)
        # O Geopandas costuma isolar o tipo corretamente usando dict raw se foi gravado como lógico,
        # mas caso venha Integer, transformamos.
        if mapping_info and mapping_info.get("pg_type") == "boolean":
            if isinstance(shp_val, bool):
                return shp_val
            if isinstance(shp_val, str):
                return shp_val.lower() in ("true", "t", "yes", "y", "1")
            if isinstance(shp_val, int):
                return shp_val == 1
                
        # String padrão / numerico
        return shp_val

    def map_record(self, shp_class_name: str, full_shp_name: str, record: ShapefileRecord) -> Optional[PostGISRecord]:
        """
        Converte ShapefileRecord -> PostGISRecord buscando a tabela no Mapeamento
        e cruzando os atributos validos. Retorna None se a classe não estiver mapeada.
        """
        # Obter nome destino da tabela base
        pg_table_base = self.rules.get_pg_table(shp_class_name)
        if not pg_table_base:
            # Classes do shape desconhecidas para o banco nao sao importadas
            return None
            
        # O banco de dados PostGIS da EDGV 3.0 contém as tabelas dividas pela geometria
        # usando o sufixo _A, _L, _P igual os ShapeFiles. Repassando ao pg_table:
        suffix = full_shp_name[-2:].lower()
        if suffix in ("_a", "_l", "_p"):
            pg_table = f"{pg_table_base}{suffix}"
        else:
            pg_table = pg_table_base
            
        pg_attributes = {}
        
        # Iterar todos os atributos extraídos pelo GeoPandas
        for shp_attr_name, shp_value in record.attributes.items():
            # ID é chave primária, no PostGIS do EDGV, as PK são seriais autogeradas 'id'
            # Geralmente não forçamos INSERT na PK pois pode conflitar com a sequence do banco.
            if shp_attr_name.upper() == "ID":
                continue
                
            attr_mapping = self.rules.get_attribute_mapping(shp_class_name, shp_attr_name)
            
            # Se o atributo existe no modelo do Shapefile e tem correspondência no PG
            if attr_mapping:
                pg_col_name = attr_mapping["pg_attr"]
                pg_val = self._transform_value(shp_value, attr_mapping)
                pg_attributes[pg_col_name] = pg_val
                
        # Inserir atributos obrigatorios pelo PostGIS que o SHP não fornece
        # E fornecer fallback case o Shapefile envie nulos (None) para campos obrigatórios
        default_fields = self.rules.get_default_fields(shp_class_name)
        for def_attr, def_val in default_fields.items():
            if def_attr not in pg_attributes or pg_attributes[def_attr] is None:
                pg_attributes[def_attr] = def_val

        # --- AUDITORIA DE FALLBACKS (Geral) ---
        feicao_id = record.attributes.get("ID", "SN")
        inconsistencies = []
        
        # Inspecionar o dicionario final que vai pro PostGIS
        for pg_col, pg_val in pg_attributes.items():
            if pg_val in (9999, "Desconhecido"):
                # Tentar achar a coluna original do SHP pra dar contexto
                raw_shp_val = "N/A"
                shp_col_name = "N/A"
                
                # Reverse mapping search
                for shp_attr, s_val in record.attributes.items():
                    amap = self.rules.get_attribute_mapping(shp_class_name, shp_attr)
                    if amap and amap["pg_attr"] == pg_col:
                        shp_col_name = shp_attr
                        raw_shp_val = str(s_val)
                        break
                
                is_prenchido = raw_shp_val != "N/A" and raw_shp_val != "None" and str(raw_shp_val).strip() not in ("", "nan")
                motivo = "Sem correspondência no Domínio" if is_prenchido else "Obrigatório (Vazio/Nulo/Inexistente no SHP)"
                
                inconsistencies.append([full_shp_name, feicao_id, shp_col_name, raw_shp_val, pg_col, str(pg_val), motivo])
        
        if inconsistencies:
            audit_file = "relatorio_inconsistencias.csv"
            file_exists = os.path.exists(audit_file)
            with open(audit_file, "a", encoding="utf-8", newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(["Classe_Shapefile", "ID_Feicao", "Coluna_SHP_Origem", "Valor_Original_SHP", "Coluna_PG", "Valor_Atribuido", "Motivo"])
                
                for inc in inconsistencies:
                    writer.writerow(inc)
                    
        return PostGISRecord(table_name=pg_table, 
                             wkt_geometry=record.wkt_geometry, 
                             attributes=pg_attributes)
