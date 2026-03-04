import json
import os
import shutil

# Precisaremos importar a inteligência do nosso preenchedor fuzzy!
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from autofill_conversao import find_best_attribute_match

# Caminhos do Dicionário
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'source-knowlegde'))
PG_MASTER = os.path.join(BASE_DIR, "edgv-3-shapefile", "master_file_300.json")
SHP_MASTER = os.path.join(BASE_DIR, "edgv-3-shapefile", "master_file_300_shp.json")

CONVERSAO_ATUAL = os.path.join(BASE_DIR, "conversao_pg-edgv-300_shp-edgv-300_completo.json")
CONVERSAO_OLD = os.path.join(BASE_DIR, "conversao_pg-edgv-300_shp-edgv-300_completo_old.json")

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def main():
    print("Iniciando Módulo de Expansão Contínua do Dicionário JSON...")
    
    # 1. Backups Padrão
    if os.path.exists(CONVERSAO_ATUAL):
        shutil.copy2(CONVERSAO_ATUAL, CONVERSAO_OLD)
        print(f"✅ Backup gerado com sucesso: {CONVERSAO_OLD}")
    else:
        print(f"❌ Erro fatal: O dicionário semente ({CONVERSAO_ATUAL}) não foi encontrado!")
        return

    # 2. Carregar Conhecimentos
    pg_data = load_json(PG_MASTER)
    shp_data = load_json(SHP_MASTER)
    conversao_data = load_json(CONVERSAO_ATUAL)
    
    # Montar indexadores para buscas ultra-rápidas das classes PostGIS / Shapefile
    # Observação Importante do PostGIS: Algumas tabelas são guardadas nas extensões auxiliares.
    pg_lookup = {}
    for pg_lista in ["classes", "extension_classes"]:
        for cls in pg_data.get(pg_lista, []):
            pg_lookup[cls['nome'].lower()] = cls
            
    shp_lookup = {c['nome'].lower(): c for c in shp_data.get('classes', [])}
    
    # Descobrir quem o dicionário base "já conhece"
    memorized_classes = {c['classe_B'].lower() for c in conversao_data.get('mapeamento_classes', [])}
    
    novas_classes_coletadas = 0
    
    # 3. Peneirar as Virgens (Órfãs) no Shapefile
    for shp_cls in shp_data.get('classes', []):
        shp_cls_name = shp_cls['nome']
        
        # O pulo do gato: Se a classe do Exército Shapefile AINDA não estiver no JSON
        if shp_cls_name.lower() not in memorized_classes:
            
            # Precisamos achar quem ela é no PostGIS usando os mesmos prefixos/letras
            pg_match_name = find_best_attribute_match(shp_cls_name, list(pg_lookup.values()))
            
            # Só podemos preencher colunas se a tabela Shape existir no Postgis (Postgis é o manda-chuva do design)
            if pg_match_name and pg_match_name.lower() in pg_lookup:
                
                print(f"🔎 Expandindo Dicionário para Nova Tabela: {shp_cls_name} -> {pg_match_name}")
                pg_cls_def = pg_lookup[pg_match_name.lower()]
                
                novo_bloco = {
                    "classe_A": pg_match_name,
                    "classe_B": shp_cls_name,
                    "mapeamento_atributos": []
                }
                
                # 4. Magia Pura: Mandar a IA criar os mapeamentos das Colunas Dessa Nova Tabela
                for attr_shp in shp_cls.get("atributos", []):
                    nome_coluna_shp = attr_shp['nome']
                    
                    # Ignoramos Padrões da biblioteca Shape
                    if nome_coluna_shp in ['ID', 'GEOAPROX', 'NOME', 'geom', 'geometry']:
                        continue
                        
                    # Busca coluna parceira usando motor analítico Fuzzy/Override
                    nome_parceira_pg = find_best_attribute_match(nome_coluna_shp, pg_cls_def.get('atributos', []))
                    
                    if nome_parceira_pg:
                        novo_bloco["mapeamento_atributos"].append({
                            "attr_A": nome_parceira_pg,
                            "attr_B": nome_coluna_shp,
                            "observacao_gerada": "Expansor Autônomo via Fuzzy/Prefixos"
                        })
                        
                # Adiciona o tijolo construído no Castelo do Dicionário
                conversao_data['mapeamento_classes'].append(novo_bloco)
                novas_classes_coletadas += 1

    # 5. Sobrescrever o Oficial
    if novas_classes_coletadas > 0:
        save_json(conversao_data, CONVERSAO_ATUAL)
        print(f"🎉 SUCESSO! A Inteligência expandiu o Cérebro preenchendo as {novas_classes_coletadas} classes órfãs.")
    else:
        print("Tudo já está 100% preenchido no Mestre! Nada novo foi adicionado.")

if __name__ == "__main__":
    main()
