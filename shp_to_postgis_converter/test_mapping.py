import geopandas as gpd
import pandas as pd
from src.domain.mapping_rules import MappingRules
from src.application.mapper_service import GeometricAttributeMapper
from src.domain.entities import ShapefileRecord

def test_mapping():
    rules = MappingRules("config/mapping_shp_to_pg.json")
    mapper = GeometricAttributeMapper(rules)
    
    shp_path = r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\banco-edgv-3-sahpefile-populado\CBGE_Trecho_Arruamento_L.shp"
    gdf = gpd.read_file(shp_path)
    
    print("Testing mapping on first 10 rows:")
    for i, row in gdf.head(10).iterrows():
        # recreate how shapefile_reader.py does it
        attributes = {}
        for col in gdf.columns:
            if col != "geometry":
                val = row[col]
                # convert numpy types to native types if needed, similar to reader
                if pd.isna(val):
                    val = None
                attributes[col] = val
                
        record = ShapefileRecord(attributes=attributes, wkt_geometry="LINESTRING EMPTY")
        pg_record = mapper.map_record("CBGE_Trecho_Arruamento", "CBGE_Trecho_Arruamento_L", record)
        
        if pg_record:
            print(f"--- Row {i} ---")
            for k, v in pg_record.attributes.items():
                if v == 9999 or v == 0 or v == "Desconhecido":
                    orig_val = attributes.get(k.upper())
                    
                    # try to find original attribute name in rules
                    orig_attr = None
                    mapping_info = None
                    cls_info = rules._class_map.get("CBGE_Trecho_Arruamento")
                    if cls_info:
                        for attr in cls_info["attributes"]:
                            if attr["pg_attr"] == k:
                                orig_attr = attr["shp_attr"]
                                mapping_info = attr
                                break
                                
                    if orig_attr:
                        raw_val = attributes.get(orig_attr)
                        print(f"Fallback {k}={v} <- {orig_attr}='{raw_val}'")
                        if mapping_info and mapping_info.get("is_domain"):
                            print(f"   Domain map keys: {list(mapping_info['value_map'].keys())[:5]}...")

if __name__ == "__main__":
    test_mapping()
