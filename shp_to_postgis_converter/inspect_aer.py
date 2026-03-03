import geopandas as gpd
from src.domain.mapping_rules import MappingRules
from src.application.mapper_service import GeometricAttributeMapper
from src.domain.entities import ShapefileRecord

def inspect_aer():
    shp_path = r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\banco-edgv-3-sahpefile-populado\AER_Pista_Ponto_Pouso_A.shp"
    gdf = gpd.read_file(shp_path)
    
    rules = MappingRules("config/mapping_shp_to_pg.json")
    mapper = GeometricAttributeMapper(rules)
    
    with open("aer_dump.txt", "w", encoding="utf-8") as f:
        f.write(f"Total rows: {len(gdf)}\n\n")
        
        for i, row in gdf.head(5).iterrows():
            f.write(f"--- ROW {i} RAW ---\n")
            attributes = {}
            for col in gdf.columns:
                if col != 'geometry':
                    val = row[col]
                    attributes[col] = val
                    f.write(f"{col}: {repr(val)}\n")
                    
            record = ShapefileRecord(attributes=attributes, wkt_geometry="POLYGON EMPTY")
            pg_record = mapper.map_record("AER_Pista_Ponto_Pouso", "AER_Pista_Ponto_Pouso_A", record)
            
            f.write("\n--- RESULTING PG ATTRIBUTES ---\n")
            if pg_record:
                for k, v in pg_record.attributes.items():
                    f.write(f"{k} = {v}\n")
            else:
                f.write("Class not mapped.\n")
            f.write("\n==============================\n")

if __name__ == "__main__":
    inspect_aer()
