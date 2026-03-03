import json

class MappingRules:
    """
    Carrega o JSON gerado dinamicamente e disponibiliza métodos
    rápidos para consultar como um atributo ou classe deve ser mapeado.
    """
    def __init__(self, mapping_filepath: str):
        with open(mapping_filepath, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            
        # Otimizar busca por classe
        self._class_map = {
            cls["shp_class"]: cls for cls in self.data["class_mapping"]
        }

    def get_pg_table(self, shp_class_name: str) -> str:
        """
        Retorna o nome da tabela PostGIS (destino) baseando-se no nome do Shapefile.
        """
        cls_info = self._class_map.get(shp_class_name)
        return cls_info["pg_table"] if cls_info else None

    def get_attribute_mapping(self, shp_class_name: str, shp_attr_name: str) -> dict:
        """
        Retorna as regras de conversão para um atributo específico.
        """
        cls_info = self._class_map.get(shp_class_name)
        if not cls_info:
            return None
            
        for attr in cls_info["attributes"]:
            if attr["shp_attr"] == shp_attr_name:
                return attr
        return None
        
    def get_default_fields(self, shp_class_name: str) -> dict:
        """
        Retorna o dicionário de campos default requeridos (NOT NULL) pelo PostGIS
        que naturalmente não possuem contrapartida no arquivo shapefile.
        """
        cls_info = self._class_map.get(shp_class_name)
        if cls_info:
            return cls_info.get("default_fields", {})
        return {}
