# 🗺️ WIKI DO PROJETO: Guia para Usuários Intermediários (Analistas GIS e Operadores)

Se você é um usuário intermediário (Geógrafo, Analista de SIG, Operador de Dados Acostumado com FME/QGIS), este guia vai detalhar o funcionamento do nosso "cérebro" de conversão. Aqui você aprenderá como as geometrias mudam, como funciona a tradução de atributos e as manutenções rotineiras sem precisar programar.

---

## 1. O Pipeline (Caminho do Dado)

O papel do software na sua rotina é atuar como um "FME Automatizado e Focado":
1. **Entrada (GeoPandas):** O script `main.py` usa a biblioteca `geopandas` subjacente para abrir seu Shapefile e extrair os Vértices Geométricos transformando a geometria em Texto (WKT: Well-Known Text, ex: `POLYGON((0 0, 0 1, 1 1, 1 0, 0 0))`).
2. **Transformação (Regras de Domínio):** Uma feição passa por um tradutor, como uma "Lupa". A lupa pergunta: *"Se o TIPO_PAV no shapefile era 'Asfalto', que número (Domínio) ele é na EDGV PostgreSQL?"* e devolve `1`.
3. **Carga (Output SQL):** O sistema envelopa esse WKT e os domínios mapeados num bloco SQL gigante `INSERT INTO...` que o servidor PostGIS consegue rodar processando todas as linhas numa pancada de milissegundos.

## 2. Lidando com Arquivos JSON (Onde Moram Suas Regras)

Você, Analista, passará o tempo interagindo na pasta `source-knowlegde`. Nela, os três arquivos colossais mais importantes são:
* `master_file_300.json`: É a "Bíblia" de Destino. Dita como as mais de 170 tabelas e seus domínios e cardinalidades vivem no banco edgv topográfico PostGIS. **NUNCA DEVE SER EDITADO!**
* `master_file_300_shp.json`: O mesmo formato de dita-regras, mas é a fotografia oficial das tabelas e do design original do arquivo Shapefile do Exército.
* 🧠 **`conversao_pg-edgv-300_shp-edgv-300_completo.json`**: O Cérebro! É aqui que um Analista arruma as coisas.

**Como Injetar uma Tradução Manual?**
Se você notar que uma palavra do seu Shapefile não está traduzindo para um domínio (ex: Valor "Estrada de Terra"), abra esse Cérebro Completo no VSCode, aperte `CTRL+F`, busque por ex: `trecho_rodoviario`, e adicione sua rota lá no dicionário da linha, respeitando a abertura e fechamento das aspas `"Estrada de Terra": 4`.

Após interagir e alterar manualmente o Cérebro Maior, sempre recompile para uma cartilha limpa usando o atalho (com a raiz do projeto sendo em `shp_to_postgis_converter`):
```bash
python scripts/generate_mapping.py
```

## 3. Override de Colunas Desconhecidas (O Bypass)

O sistema lida com 90% das correspondências de campos de um jeito sozinho usando "Heurísticas" e "Motor Astúcia/Fuzzy". Mas, se de repente, você recebeu do seu contratante um Lote com shapefile onde a coluna Canteiro Divisório veio escrita como `DIVISOR_CN`, e o Cérebro surtou sem saber para onde enviar essa string, você pode intervir criando um **Override Manual**.

1. Edite o arquivo Python: `shp_to_postgis_converter/autofill_conversao.py` 
2. Localize lá no início a palavra `overrides = {` e crie uma linha ensinando-o: `'divisor_cn': 'canteirodivisorio'`
3. Salve e execute a recompilação total no console:
`python autofill_conversao.py` e depois em seguida `python scripts/generate_mapping.py`. O sistema eternizou a correlação da sigla bizarra.

## 4. Auditoria de Feições Seguras (Relatório de Fallbacks)
Às vezes você exporta de um geoprocesso do QGIS e não gera a coluna obrigatória "jurisdição" das pontes. Isso causaria falha na Transação no Banco e o processo do antigo IBGE ou Exército travaria por causa de uma ponte órfã no meio de milhares.
**A Solução de Resgate:** O sistema intercepta o pânico e coloca ali "9999" (Desconhecido), permitindo gravar os milhares de geometrias. Em seguida, ele compõe para você, analista, um painel vivo: a planilha O relatório gerado **`relatorio_inconsistencias.csv`** relatará: *"A Ponte de ID 445 foi salva, mas com jurisdição Desconhecida, verifique-a no seu SIG"*. 

Você só audita as métricas finais sem interromper fluxos!
