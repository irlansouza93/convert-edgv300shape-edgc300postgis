from typing import List
from src.domain.entities import PostGISRecord
import math
import pandas as pd

class SqlScriptWriter:
    """
    Gera instruções INSERT baseadas nas classes e atributos mapeados.
    """
    def __init__(self, output_filepath: str, schema_name: str = "edgv"):
        self.output_filepath = output_filepath
        self.schema_name = schema_name
        # Limpamos ou recriamos o arquivo inicial
        with open(self.output_filepath, 'w', encoding='utf-8') as f:
            f.write(f"-- Arquivo SQL de migracao automatica de Shapefile EDGV para PostGIS\n")
            f.write(f"BEGIN;\n\n")

    def _format_value(self, val, pg_type: str) -> str:
        """
        Formata um valor Python para a correspondente String SQL suportada pelo PostGIS.
        """
        # Tratar nulls e NaNs vindos do pandas/geopandas
        if pd.isna(val) or val is None:
            return "NULL"
            
        # Booleans
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        
        # Numéricos
        if isinstance(val, (int, float)):
            return str(val)
        
        # Strings - Tratar aspas simples no meio do texto
        val_str = str(val)
        val_str = val_str.replace("'", "''")
        return f"'{val_str}'"

    def write_inserts(self, records: List[PostGISRecord]):
        """
        Escreve lotes de inserts no arquivo para melhorar o desempenho de execução via script.
        Essa camada lida estritamente com a formatação SQL.
        """
        if not records:
            return

        with open(self.output_filepath, 'a', encoding='utf-8') as f:
            for record in records:
                # O master_file_300 dita que as geometricas da EDGV sao guardadas na coluna 'geom'
                # Todas EPSG:4674 (SIRGAS 2000)
                columns = []
                values = []
                
                for col_name, val in record.attributes.items():
                    columns.append(col_name)
                    # Não temos acesso ao tipo exato do campo aqui pois o Mapper que deveria 
                    # fazer a conversao correta final, então formatamos baseando-se no tipo do dado processado.
                    values.append(self._format_value(val, "unknown"))
                
                # Tratar geometria
                if record.wkt_geometry:
                    columns.append("geom")
                    # No EDGV 3.0 todos estão no SRS 4674
                    values.append(f"ST_GeomFromText('{record.wkt_geometry}', 4674)")
                
                cols_str = ", ".join(columns)
                vals_str = ", ".join(values)
                
                # As tabelas EDGV contêm schema (geralmente edgv as origin maps)
                # O master config diz "schema_dados": "edgv"
                sql = f"INSERT INTO {self.schema_name}.{record.table_name} ({cols_str}) VALUES ({vals_str});\n"
                f.write(sql)
                
    def close(self):
        """Finaliza a transação do script gerado."""
        with open(self.output_filepath, 'a', encoding='utf-8') as f:
            f.write(f"\nCOMMIT;\n")
