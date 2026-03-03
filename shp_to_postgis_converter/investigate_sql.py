import re
from collections import Counter

def analyze_sql():
    # ler o sql
    sql_file = "output_edgv.sql"
    
    fallback_pattern = re.compile(r'\b(9999|0|\'Desconhecido\')\b')
    
    table_stats = Counter()
    
    try:
        with open(sql_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("INSERT INTO"):
                    # Extrair nome da tabela
                    match = re.search(r'INSERT INTO (\w+\.\w+)', line)
                    if match:
                        table = match.group(1)
                        # Checar quantos fallbacks tem na linha
                        fallbacks = fallback_pattern.findall(line)
                        if fallbacks:
                            table_stats[table] += 1
                            if table_stats[table] <= 2:
                                print(f"Sample from {table}:")
                                print(line[:200] + "...")
                                
        print("\nTables with fallback values (9999, 0, 'Desconhecido'):")
        for table, count in table_stats.most_common(10):
            print(f"{table}: {count} inserts with fallbacks")
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    analyze_sql()
