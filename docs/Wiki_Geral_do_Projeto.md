# 🌍 WIKI DO PROJETO: Conversor Inteligente EDGV (Shapefile ➡️ PostGIS)

Bem-vindo(a) ao Guia Geral do Projeto! Este documento foi redigido de forma simples, livre de "tecniquês" excessivo, focado em explicar a qualquer pessoa (geógrafos, analistas, novos desenvolvedores) **o que é o sistema**, **por que ele existe**, e **como operá-lo no dia a dia**.

---

## 1. O Que É e Por Que Existe?

O Exército e as entidades governamentais do Brasil utilizam um padrão rigoroso para desenhar mapas, chamado **EDGV (Especificação Técnica para Estruturação de Dados Geoespaciais Vetoriais)**.

Imagine que você recebeu milhares de arquivos velhos de mapas em formato **Shapefile** e você precisa colocá-los dentro de um Banco de Dados moderno e veloz chamado **PostGIS**. Contudo, você não pode simplesmente "jogar" os mapas lá dentro. O Banco de Dados PostGIS exige que os nomes das colunas e os números (códigos) obedeçam friamente o Padrão EDGV.

**O Problema que resolvemos:** Fazer essa tradução (de / para) de forma manual através de softwares como QGIS (ou usando o FME, que é pago e caro) exigiria olhar centenas de milhares de linhas para formatar as coisas ou criar modelos arrastando blocos o dia todo inteiro.
**A Nossa Solução:** Construímos um Conversor Inteligente usando linguagem Python. Ele usa Inteligência Computacional e regras precisas para ler seus Shapefiles "brutos" e imprimir as instruções já mastigadas, perfeitas, diretamente para serem injetadas no banco final.

---

## 2. A Estrutura das Pastas (Como a casa está organizada?)

O projeto obedece ao estado-da-arte de organização de pastas. Ele é dividido em três "mundos" para que não haja confusão:

* 📁 **`docs/` (A Biblioteca):** Onde você está lendo isso. Guarda as Leis de código, Histórias do projeto e FAQs.
* 📁 **`source-knowlegde/` (O Cérebro e a Matéria Prima):** Aqui ficam os arquivos brutos. Ficam os famosos "Master Files", que são os Dicionários Oficiais da EDGV em formato `.json` (A "gramática" do Banco PostGIS e a do Shapefile). Também é aqui dentro fica o **`conversao_pg-edgv-300_shp-edgv-300_completo.json`**, que é a nossa Enciclopédia Titânica traduzindo tabela por tabela. A pasta *banco-edgv-3-shapefile-populado* guarda todos os seus arquivos físicos de mapa que você deseja converter.
* 📁 **`shp_to_postgis_converter/` (A Fábrica/Motor):** Aqui dentro ficam as engrenagens. Os códigos Python que trabalham, a lista de configurações e os robôs fiscais que testam as coisas.

---

## 3. O Passo a Passo de Execução Diária

Como esse é um sistema focado em automação zero-configurações (Plug and Play), operá-lo é uma tarefa de 3 etapas no terminal/linha de comandos:

### Etapa 1: Preparar as malas
1. Reúna todos os seus mapas/shapefiles que quer migrar (arquivos `.shp`, `.dbf`, `.shx`, etc).
2. Cole tudo dentro da pasta `source-knowlegde/banco-edgv-3-shapefile-populado`.

### Etapa 2: Ligar o Motor Principal
Abra o terminal/Prompt do seu computador dentro da pasta `shp_to_postgis_converter` e digite o comando abaixo (garanta que seu ambiente Python / `venv` esteja ativo):
```bash
python main.py
```
Esse comando lerá todos os seus shapefiles, enviará as linhas para o tradutor e construirá rapidamente na pasta o arquivo **`output_edgv.sql`**.

### Etapa 3: Coletar os Frutos
* **O Código Pronto:** O arquivo `output_edgv.sql` gerado terá instruções `INSERT INTO` em massa. Você só precisa abri-lo e roda-lo no seu Banco de Dados (usando programas como pgAdmin, DBeaver, DBeaver, etc.) e as tabelas lá serão magicamente povoadas já sob as rédeas da EDGV 3.0.
* **O Relatório Visor:** Na mesma pasta do motor, você verá o `relatorio_inconsistencias.csv`. Se o sistema encontrou em algum do seus poligonos uma "Classe OBRIGATÓRIA" vazia, pra não quebrar o banco, o nosso sistema enviou ela como "Desconhecido" (código 9999 Seguro) e reportou neste CSV a exata placa ou ponte que carecia de digitação, permitindo ao Analista auditar o erro num QGIS sabendo onde apontar.

---

## 4. O Canivete Suíço da IA (Máquina Extensora)

O projeto é Vivo. Ele usa de algoritmos matemáticas (Machine Learning Fuzzy) para se virar com o desconhecido. Se um novo arquivo EDGV chegar, o software provê três comandos secundários extremamente valiosos (a serem usados na pasta `shp_to_postgis_converter/`):

* 🔮 **O Extrator (`python scripts/expand_conversao_json.py`):** 
Se você injetar tabelas de classe "NOVAS" no banco ou usar um modelo novo (ex: Topo EDGV), esse comando lê os novos Manuais Oficiais e, tentando adivinhar as conexões pelas letras, preenche magicamente a enciclopédia inteira (e gera backup do velho).
* ⚙️ **O Compilador (`python scripts/generate_mapping.py`):**
Seja porque a IA acima rodou e atualizou a enciclopédia, ou porque você mexeu na folha manualmente (conforme nosso arquivo `FAQ_Orientacao_Usuario_Leigo.md`), esse comando comprime os dados colossais e gera um modelo "Leve e Rápido" chamado `config/mapping_shp_to_pg.json` que é engolido instantaneamente pelo nosso `main.py` de execução diária.
* 🤖 **O Fiscal de Fronteira (`pytest tests/test_completude_json.py -v`):** 
Bateu a dúvida se os dicionários têm "Buracos Cegos"? Rodando esse teste, o Robô audita se existem matrizes de tradução órfãs que escaparam, avisando com 100% de precisão o que falta traduzir.

### Entendeu?
Ele é muito mais que um conversor, é um Dicionário Vivo de Modelagem de Atributos e um Construtor Unificado! Você pode consultar a história do porquê certas decisões foram tomadas nos demais arquivos markdown formatados nesta pasta de `/docs`.
