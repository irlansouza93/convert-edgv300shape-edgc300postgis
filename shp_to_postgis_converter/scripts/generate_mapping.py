import json
import os

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def to_snake_case(name):
    """
    Converte nomes em CamelCase (Formato Shapefile) para snake_case (Formato PostGIS).
    Exemplo: Subest_Transm_Distrib_Energia_Eletrica -> subest_transm_distrib_energia_eletrica
    """
    return name.lower()

def main():
    base_dir = r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\edgv-3-shapefile"
    shp_master_file = os.path.join(base_dir, "master_file_300_shp.json")
    pg_master_file = os.path.join(base_dir, "master_file_300.json")
    
    # 1. Carregar os Master Files e as Regras de Conversao
    print("Carregando master files...")
    shp_data = load_json(shp_master_file)
    pg_data = load_json(pg_master_file)
    
    conversao_path = r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\source-knowlegde\conversao_pg-edgv-300_shp-edgv-300_completo.json"
    conversao_data = load_json(conversao_path)
    
    # Dicionario de regras de conversão por classe (Shapefile -> Mapeamentos)
    conversao_dict = {
        m["classe_B"].upper(): m for m in conversao_data.get("mapeamento_classes", [])
    }
    
    # Dicionário útil para lookup de classes do PostGIS por nome
    pg_classes_dict = {}
    for cl_list in ["classes", "extension_classes"]:
        for cls in pg_data.get(cl_list, []):
            pg_classes_dict[cls["nome"].lower()] = cls
    
    # Dicionário útil para lookup de domínios do PostGIS
    pg_domains_dict = {
        dom["nome"]: dom for dom in pg_data["dominios"]
    }
    
    mapping_result = {
        "metadata": {
            "source": "EDGV 3.0 SHP",
            "target": "EDGV 3.0 PostGIS",
            "description": "Mapeamento dinâmico gerado invertendo as lógicas do FME, cobrindo todos os atributos"
        },
        "class_mapping": [],
        "domain_mapping": {}
    }
    
    # 2. Processar cada classe do Shapefile
    for shp_cls in shp_data["classes"]:
        shp_class_name = shp_cls["nome"]
        shp_category = shp_cls["categoria"]
        
        # O nome real do Shapefile no nível de arquivo contém o prefixo da categoria + classe.
        # Ex: "AER_Pista_Ponto_Pouso"
        full_shp_class_name = f"{shp_category}_{shp_class_name}"
        
        # O nome no master_file_300.json (PostGIS) é apenas o nome da classe em minúsculo
        # Ex: "pista_ponto_pouso" (SEM o "aer_")
        pg_class_name = shp_class_name.lower()
        
        # O nome da tabela física no banco em si combina os dois
        pg_table_name = full_shp_class_name.lower()
        
        # Verificar se a classe existe no modelo PostGIS
        if pg_class_name in pg_classes_dict:
            pg_cls_info = pg_classes_dict[pg_class_name]
            
            class_map_entry = {
                "shp_class": full_shp_class_name,
                "pg_table": pg_table_name,
                "pg_class_def": pg_class_name,
                "attributes": [],
                "default_fields": {}
            }
            
            # 3. Mapear Atributos
            pg_attr_dict = {attr["nome"]: attr for attr in pg_cls_info["atributos"]}
            
            # Recuperar as regras de conversão manual/autofill se existirem para esta classe
            regras_cls = conversao_dict.get(full_shp_class_name.upper(), {})
            
            attr_translations = {}
            # Armazena globalmente a traducao com base no nome da coluna original (SHP)
            val_translations_global = {}
            
            # --- NOVA LÓGICA DE DADOS GLOBAIS ÓRFÃOS ---
            # Carregar mapeamentos da raiz do json que o usuário forneceu como dicionários universais
            for g_attr in conversao_data.get("mapeamento_atributos", []):
                if "traducao" in g_attr:
                    val_translations_global[g_attr["attr_B"]] = {
                        str(t["valor_B"]).strip().lower(): t["valor_A"] for t in g_attr["traducao"]
                    }
                    
            # --- DADOS ESPECÍFICOS DA CLASSE ---
            for m in regras_cls.get("mapeamento_atributos", []):
                attr_translations[m["attr_B"]] = m["attr_A"]
                if "traducao" in m:
                    # Dicionário de tradução manual: { "valor string shp em minúsculas": código_inteiro_pg }
                    val_translations_global[m["attr_B"]] = {
                        str(t["valor_B"]).strip().lower(): t["valor_A"] for t in m["traducao"]
                    }
            
            for shp_attr in shp_cls["atributos"]:
                shp_attr_name = shp_attr["nome"]
                
                # Identificar o nome no PostGIS, usando tradutor se houver, senao default pra lowercase
                if shp_attr_name in attr_translations:
                    pg_attr_name = attr_translations[shp_attr_name]
                else:
                    pg_attr_name = shp_attr_name.lower()
                
                # O ID do shape é mapeado para 'id' no PostGIS ou gerado automaticamente, trataremos depois
                if shp_attr_name == "ID":
                    continue
                    
                if pg_attr_name in pg_attr_dict:
                    pg_attr_info = pg_attr_dict[pg_attr_name]
                    is_domain = False
                    domain_name = None
                    tipo_pg = pg_attr_info["tipo"]
                    
                    attr_entry = {
                        "shp_attr": shp_attr_name,
                        "pg_attr": pg_attr_name,
                        "pg_type": tipo_pg,
                        "is_domain": False
                    }
                    
                    if tipo_pg in ("smallint", "integer"):
                        domain_key_from_pg = pg_attr_info.get("mapa_valor")
                        
                        possible_domain_names = []
                        if domain_key_from_pg:
                            possible_domain_names.append(domain_key_from_pg)
                            
                        for pd_name in possible_domain_names:
                            if pd_name in pg_domains_dict:
                                is_domain = True
                                domain_name = pd_name
                                break
                                
                        if is_domain:
                            dom_info = pg_domains_dict[domain_name]
                            reverse_map = {}
                            for val in dom_info["valores"]:
                                key_str = val["value"].strip()
                                val_int = val["code"]
                                reverse_map[key_str] = val_int
                                reverse_map[key_str.upper()] = val_int
                                reverse_map[key_str.lower()] = val_int
                            
                            # Injetar a lista de traduções manuais para estender/sobrepor as padrões
                            # Agora procuramos na piscina global usando a chave raiz do SHP
                            if shp_attr_name in val_translations_global:
                                for t_val_str, t_val_int in val_translations_global[shp_attr_name].items():
                                    reverse_map[t_val_str] = t_val_int
                                    reverse_map[t_val_str.upper()] = t_val_int
                                    reverse_map[t_val_str.lower()] = t_val_int
                                    
                            attr_entry["is_domain"] = True
                            attr_entry["domain_name"] = domain_name
                            attr_entry["value_map"] = reverse_map
                            
                            # Definir um valor padrao seguro ("Desconhecido" / 9999) como fallback point dentro da coluna
                            default_val = 9999
                            for dom_val in dom_info["valores"]:
                                val_str = dom_val["value"].lower()
                                if val_str.startswith("desconhecid"):
                                    default_val = dom_val["code"]
                                    break
                                elif "aplicável" in val_str or "aplicavel" in val_str:
                                    default_val = dom_val["code"]
                            
                            if "valores" in pg_attr_info:
                                allowed_codes = [v["code"] for v in pg_attr_info["valores"]]
                                if default_val not in allowed_codes:
                                    default_val = 9999
                                    
                            attr_entry["default_value"] = default_val
                            
                    # Se não for dominio, mas for mapeado e o FME enviar NaN/nulo:
                    # Garantimos um valor seguro SE for cardinalidade obrigatória (1..1) limitando sujar dados nullable.
                    if "default_value" not in attr_entry:
                        is_mandatory = pg_attr_info.get("cardinalidade") == "1..1"
                        
                        if is_mandatory:
                            pg_type_lower = tipo_pg.lower()
                            if pg_type_lower in ("boolean", "booleano"):
                                attr_entry["default_value"] = False
                            elif pg_type_lower in ("smallint", "integer"):
                                attr_entry["default_value"] = 9999
                            elif "varchar" in pg_type_lower or "text" in pg_type_lower:
                                attr_entry["default_value"] = "Desconhecido"
                            elif pg_type_lower in ("real", "double precision", "numeric"):
                                attr_entry["default_value"] = 0.0
                        
                    class_map_entry["attributes"].append(attr_entry)

            # 4. Adicionar default values para as colunas obrigatorias no BD, como fallback para nulos (NaN)
            # Apenas catalogamos as obrigatórias para servirem como escudo quando o DataFrame vomitar None.
            mapped_pg_attrs = {attr["pg_attr"] for attr in class_map_entry["attributes"]}
            for pg_attr_info in pg_cls_info.get("atributos", []):
                pg_attr_name = pg_attr_info["nome"].lower()
                # 'id' é gerado automaticamente pelo banco, 'geom' tratamos no python
                if pg_attr_name in mapped_pg_attrs or pg_attr_name in ("id", "geom", "geometria"):
                    continue
                    
                # Se for cardinalidade 1..1 (obrigatorio)
                if pg_attr_info.get("cardinalidade") == "1..1":
                    pg_type = pg_attr_info["tipo"].lower()
                    if pg_type == "boolean" or pg_type == "booleano":
                        class_map_entry["default_fields"][pg_attr_name] = False
                    elif pg_type == "smallint" or pg_type == "integer":
                        # Identificar o código para Desconhecido (geralmente 9999, 0 ou 99)
                        default_val = 9999
                        dom_mapped = pg_attr_info.get("mapa_valor")
                        if dom_mapped and dom_mapped in pg_domains_dict:
                            for dom_val in pg_domains_dict[dom_mapped]["valores"]:
                                val_str = dom_val["value"].lower()
                                if val_str.startswith("desconhecid"):
                                    default_val = dom_val["code"]
                                    break
                                elif "aplicável" in val_str or "aplicavel" in val_str:
                                    default_val = dom_val["code"] 
                        
                        # Override local: Se o atributo tem sua lista branca de valores limitados (ex: finalidadepatio= [3])
                        # E o nosso "desconhecido" (ex: 0) mapeado globalmente nao for desta lista, voltamos para 9999 (EDGV universal check)
                        if "valores" in pg_attr_info:
                            allowed_codes = [v["code"] for v in pg_attr_info["valores"]]
                            if default_val not in allowed_codes:
                                default_val = 9999
                        
                        class_map_entry["default_fields"][pg_attr_name] = default_val
                    elif "varchar" in pg_type or "text" in pg_type:
                        class_map_entry["default_fields"][pg_attr_name] = "Desconhecido"
                    elif pg_type == "real" or pg_type == "double precision":
                        class_map_entry["default_fields"][pg_attr_name] = 0.0

            mapping_result["class_mapping"].append(class_map_entry)
        else:
            print(f"AVISO: Classe {pg_class_name} não encontrada no modelo PostGIS.")
            
            
    # Criar um arquivo de saída
    output_path = r"c:\Users\irlan\OneDrive\Área de Trabalho\mapeamento-fme\shp_to_postgis_converter\config\mapping_shp_to_pg.json"
    with open(output_path, "w", encoding="utf-8") as out_f:
        json.dump(mapping_result, out_f, indent=4, ensure_ascii=False)
        
    print(f"Mapeamento gerado com sucesso em {output_path}")

if __name__ == "__main__":
    main()
