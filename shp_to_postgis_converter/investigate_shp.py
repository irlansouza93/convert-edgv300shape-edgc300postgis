import geopandas as gpd

def inspect_shp(shp_path):
    print(f"\n--- Inspecting {shp_path} ---")
    gdf = gpd.read_file(shp_path)
    if len(gdf) > 0:
        row = gdf.iloc[0]
        for col in gdf.columns:
            if col != 'geometry':
                val = row[col]
                print(f"{col} ({type(val).__name__}): {val}")
    else:
        print("Empty shapefile.")

if __name__ == "__main__":
    shp1 = r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\banco-edgv-3-sahpefile-populado\AER_Pista_Ponto_Pouso_A.shp"
    shp2 = r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\banco-edgv-3-sahpefile-populado\CBGE_Trecho_Arruamento_L.shp"
    
    inspect_shp(shp1)
    inspect_shp(shp2)
