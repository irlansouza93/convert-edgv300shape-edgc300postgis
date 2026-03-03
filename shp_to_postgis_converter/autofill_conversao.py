import json
import difflib

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def build_class_lookup(master_pg):
    # master_pg has a 'classes' key somewhere
    lookup = {}
    for cls in master_pg.get('classes', []):
        nome = f"{cls['categoria']}_{cls['nome']}".lower()
        lookup[nome] = cls
    return lookup

def build_shp_class_lookup(master_shp):
    lookup = {}
    for cls in master_shp.get('classes', []):
        nome = f"{cls['categoria']}_{cls['nome']}".upper()
        lookup[nome] = cls
    return lookup

def find_best_attribute_match(shp_attr, pg_attrs):
    shp_lower = shp_attr.lower()
    
    # Exclude basic ones that map directly
    if shp_lower in [p['nome'].lower() for p in pg_attrs]:
        return shp_lower
        
    # Attempt prefix match
    candidates = [p['nome'] for p in pg_attrs if p['nome'].startswith(shp_lower)]
    if len(candidates) == 1:
        return candidates[0]
        
    # Attempt fuzzy match
    pg_attr_names = [p['nome'] for p in pg_attrs]
    matches = difflib.get_close_matches(shp_lower, pg_attr_names, n=1, cutoff=0.6)
    if matches:
        return matches[0]
        
    # Common manual overrides based on EDGV standards
    overrides = {
        'situaespac': 'situacaoespacial',
        'situafisic': 'situacaofisica',
        'matconstr': 'matconstr',
        'operacion': 'operacional',
        'revest': 'revestimento',
        'tipopav': 'tipopavimentacao',
        'cantdiv': 'canteirodivisorio',
        'tipopista': 'tipopista',
        'usopista': 'usopista',
        'homolog': 'homologacao',
        'adm': 'administracao',
        'concess': 'concessionaria',
        'jurisdicao': 'jurisdicao'
    }
    
    if shp_lower in overrides and overrides[shp_lower] in pg_attr_names:
        return overrides[shp_lower]
        
    return None

def main():
    pg_master = load_json(r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\edgv-3-shapefile\master_file_300.json")
    shp_master = load_json(r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\edgv-3-shapefile\master_file_300_shp.json")
    conversao = load_json(r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\conversao_pg-edgv-300_shp-edgv-300.json")
    
    pg_lookup = build_class_lookup(pg_master)
    shp_lookup = build_shp_class_lookup(shp_master)
    
    for mapping in conversao.get('mapeamento_classes', []):
        cls_pg_name = mapping['classe_A'].lower()
        cls_shp_name = mapping['classe_B'].upper()
        
        pg_cls_def = pg_lookup.get(cls_pg_name)
        shp_cls_def = shp_lookup.get(cls_shp_name)
        
        if not pg_cls_def or not shp_cls_def:
            continue
            
        pg_attrs = pg_cls_def.get('atributos', [])
        shp_attrs = shp_cls_def.get('atributos', [])
        
        if 'mapeamento_atributos' not in mapping:
            mapping['mapeamento_atributos'] = []
            
        existing_mappings = {m['attr_B']: m for m in mapping['mapeamento_atributos']}
        
        for s_attr in shp_attrs:
            s_name = s_attr['nome']
            if s_name in ['ID', 'GEOAPROX', 'NOME']:
                continue # usually handled generically or perfectly matches
                
            if s_name not in existing_mappings:
                best_match = find_best_attribute_match(s_name, pg_attrs)
                if best_match:
                    mapping['mapeamento_atributos'].append({
                        "attr_A": best_match,
                        "attr_B": s_name,
                        "observacao_gerada": "Autofill por prefixo/fuzzy"
                    })

    out_path = r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\conversao_pg-edgv-300_shp-edgv-300_completo.json"
    save_json(conversao, out_path)
    print(f"Saved completed mapping to {out_path}")

if __name__ == "__main__":
    main()
