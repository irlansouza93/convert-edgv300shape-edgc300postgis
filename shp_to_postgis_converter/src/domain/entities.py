from typing import Dict, Any, List

class ShapefileRecord:
    """
    Representação de uma feição lida do Shapefile.
    Contém a geometria original em WKT e os atributos lidos.
    """
    def __init__(self, wkt_geometry: str, attributes: Dict[str, Any]):
        self.wkt_geometry = wkt_geometry
        self.attributes = attributes

class PostGISRecord:
    """
    Representação de uma feição mapeada para o banco PostGIS.
    """
    def __init__(self, table_name: str, wkt_geometry: str, attributes: Dict[str, Any]):
        self.table_name = table_name
        self.wkt_geometry = wkt_geometry
        self.attributes = attributes
