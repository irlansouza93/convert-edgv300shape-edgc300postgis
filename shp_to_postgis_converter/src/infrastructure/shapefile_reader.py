import os
import geopandas as gpd
from typing import Generator
from src.domain.entities import ShapefileRecord

class ShapefileReader:
    """
    Responsável por ler arquivos Shapefile e converter suas linhas
    (feições) para ShapefileRecord contendo as geometrias em WKT.
    """
    def __init__(self, directory_path: str):
        self.directory_path = directory_path

    def get_shapefiles(self) -> list:
        """Retorna uma lista de caminhos absolutos para todos os shapefiles no diretório."""
        shapefiles = []
        for file in os.listdir(self.directory_path):
            if file.endswith(".shp"):
                shapefiles.append(os.path.join(self.directory_path, file))
        return shapefiles

    def read_records(self, filepath: str) -> Generator[ShapefileRecord, None, None]:
        """
        Lê as feições do shapefile e as devolve de forma iterada.
        """
        try:
            # Usamos engine 'pyogrio' para maior performance se disponível
            # Mas vamos de default fiona se pyogrio nao estiver garantido.
            gdf = gpd.read_file(filepath)
            
            for index, row in gdf.iterrows():
                # Extrai a geometria como String Text (WKT)
                geom_wkt = row.geometry.wkt if row.geometry else None
                
                # Extrai apenas os atributos que não são a geometria
                attributes = {col: row[col] for col in gdf.columns if col != 'geometry'}
                
                yield ShapefileRecord(wkt_geometry=geom_wkt, attributes=attributes)
                
        except Exception as e:
            print(f"Erro ao ler o shapefile {filepath}: {e}")
