# FAQ: Guia de Entendimento Rápido do Conversor EDGV

Este documento foi criado para responder às dúvidas mais comuns sobre o funcionamento do projeto, de forma simples e direta, para que qualquer pessoa consiga operar a ferramenta sem precisar ser um especialista em programação.

---

### 01. O arquivo json fonte de conversão completa foi gerado a partir de quê? E ele é usado para o quê?
O arquivo principal (`conversao_pg-edgv-300_shp-edgv-300_completo.json`) foi gerado a partir do cruzamento dos dicionários oficiais do Exército (os "Master Files" da EDGV 3.0), que descrevem como os dados deveriam ser no Shapefile e como eles têm que ser no PostGIS. 

**Para que é usado:** Ele atua como o **Cérebro principal** da nossa aplicação. Ele guarda "de cor" todas as regras de tradução complexas, como: 
*"Se você ler a abreviação `MATCONSTR` no Shapefile, lembre-se que no PostGIS ela se chama `mat_constr`"* e *"Se no Shapefile estiver escrito 'Construída', você deve converter isso para o código numérico `5`"*.

### 02. Se eu tiver um novo banco EDGV em shape populado agora, qual seria as etapas para a conversão?
O passo a passo é extremamente rápido, pois a inteligência já está treinada:

1. **Substitua os arquivos:** Coloque seus novos arquivos shapefile completos (com os `.shp`, `.dbx`, `.prj`, etc) descompactados dentro da pasta que o sistema escuta (geralmente `source-knowlegde/banco-edgv-3-sahpefile-populado`).
2. **Execute o construtor:** Abra seu terminal/linha de comando, vá na pasta `shp_to_postgis_converter` e digite o comando: `python main.py`.
3. **Aguarde a Mágica:** O sistema lerá todo o seu novo Shapefile em segundos/minutos. Ao terminar, ele entregará o relatório `relatorio_inconsistencias.csv` (contendo alertas se seus novos dados vierem corrompidos) e o arquivo finalizado gerado na pasta.

### 03. O que eu devo fazer com o arquivo gerado `output_edgv.sql`?
Esse é o seu "Produto Final". Você deve pegar esse arquivo e executá-lo no seu banco de dados PostgreSQL (usando um gerenciador como pgAdmin, DBeaver ou a linha de comandos do PostGIS). 
Esse arquivo é puramente um roteiro pronto contendo milhares de comandos `INSERT INTO`. Quando executado no banco, fará com que as tabelas "pisquem" na tela já 100% povoadas com seus desenhos geográficos corretos e tipologias nos padrões da EDGV, poupando programas intermediários lentos.

### 04. O que são os arquivos `output.log` e `aer_dump.txt`?
Eles eram apenas "lixo eletrônico" (arquivos de rascunhos) gerados durante o desenvolvimento e os primeiros testes por nós, programadores, para ler pedaços de dados isolados (como as pistas de pouso no `aer_dump`). Eles não têm impacto nenhum na conversão oficial e **já foram devidamente deletados** na última atualização para limpar a casa.

### 05. O que é o arquivo `mapping_shp_to_pg.json`? Em que etapa ele é gerado?
Apesar do nome complexo, ele é apenas a **"Cartilha de Instruções Práticas"** da máquina.
Enquanto o nosso JSON Completo (da pergunta 1) é o cérebro gigante em constante pesquisa e evolução, a máquina precisa de algo mais leve pra ser rápida. 
**Quando é gerado:** Toda vez que executamos o arquivo `python scripts/generate_mapping.py`. Esse script lê o Cérebro Gigante e cria essa "Cartilha" purificada, organizando apenas o que importa (Ex: Tabela X, Coluna Y=Int). É essa "Cartilha" levinha que o comando principal (`main.py`) lê na hora da correria para converter 12.000 feições em 3 segundos.

### 06. Esse sistema usa machine learning? Se sim, explique como funciona aqui.
Sim, utilizamos métodos baseados em Inteligência Computacional / Algoritmos "Fuzzy" (Lógica Difusa) no arquivo `autofill_conversao.py`, que atua como o caçador de nomes das tabelas.
**Como funciona na prática:** Quando aparece uma coluna no Shapefile que nunca vimos na vida, em vez do software parar e dar a mensagem de "Erro Fatal", o algoritmo matemático procura todas as alternativas do PostGIS e calcula uma nota de semelhança (0 a 100%) entre as vogais e prefixos. Por exemplo, se ler `CANTDIV`, a IA percebe a semelhança e adivinha sozinha que você quer encaixar na coluna matemática oficial `canteirodivisorio`, sem ajuda humana.

### 07. Esse arquivo usa conhecimentos passados para poder prever os mesmos tipos de erro, ou dados inseridos manualmente?
**Ele usa a mistura perfeita dos dois!**
Para não confiarmos cegamente na IA o tempo todo, nós aplicamos uma **Trilha de Aprendizado Forçado**. O sistema tem uma lista interna prioritária chamada `overrides` (sobrescritas manuais). Se um dia a máquina errou (como na vez em que ligou `TIPOEDIF` na Guarda Municipal errado porque pareceu com outra placa), nós, humanos, informamos explicitamente a regra absoluta: `"Sempre que ler TIPOEDIF, use tipousoedif"`. O software avalia primeiro nosso "conhecimento antigo manual"; e só pede ajuda matemática à IA quando é um desafio 100% desconhecido. 

### 08. Se uma classe não for mapeada corretamente por falta de correspondência no JSON, como o usuário pode corrigir manualmente?
É muito simples e você não precisará escrever código complicado. Eis os dois cenários:

* **Cenário A (Nome da Coluna muito estranho / AI errou):**
Abra o arquivo `shp_to_postgis_converter/autofill_conversao.py`. Procure a lista de palavras chamada `overrides`. Simplesmente adicione uma linha ali: `'nome_errado_do_shapefile': 'nome_maravilhoso_do_banco'`, salve e feche.
* **Cenário B (Falta as traduções de palavras pra códigos numéricos):**
Abra o nosso Cérebro Fonte, o arquivo `source-knowlegde/conversao_pg-edgv-300_shp-edgv-300_completo.json`. Procure pelo nome da sua tabela e procure a matriz `traducao`. Adicione nela o seu novo número e o que ele significa (`"valor_A": 6, "valor_B": "Uma Categoria Nova"`). 

Sempre que ajeitar manualmente nesses arquivos, abra o terminal e "mande o robô reimprimir a cartilha de instruções" rodando:
1. `python autofill_conversao.py`  (Apenas para o Cenário A)
2. `python scripts/generate_mapping.py` (Para reconstruir a cartilha pronta pro SQL)

### 09. O arquivo `mapping_shp_to_pg` é criado a partir do JSON completo e dos Shapefiles físicos? Se eu colocar outro banco shape, ele terá que ser recriado?
**Não, ele não lê os arquivos físicos `.shp`** para ser criado. Ele é gerado cruzando unicamente as informações matemáticas do nosso "Cérebro Maior" (`conversao_completo.json`) e os esqueletos do PostGIS. 

Portanto, se o seu novo banco Shape possuir apenas linhas novas (feições) de pontes ou estradas que já existem nas regras estruturais, basta jogar na pasta e rodar imediatamente o `python main.py`.
**Quando você precisará recriar a cartilha:** Se o seu novo banco Shape trouxer uma **Categoria de Mapa Inteiramente Nova** — por exemplo, uma tabela camada chamada `Fazenda_Agricola_Poligono` que nós nunca tínhamos visto no banco anterior. Nesse cenário, você roda `python autofill_conversao.py` para a Inteligência Artificial catalogar essa tabela nova na enciclopédia, `python scripts/generate_mapping.py` para embutir na cartilha, e só depois roda o `main` para converter os dados nela contidos.

### 10. Como sei se o arquivo JSON de conversão cobriu "100%" ou se ficaram tabelas e colunas do Master Shape para trás? Tem como eu fiscalizar isso com um comando?
Sim! Pensando em segurança, deixamos um "Robô Fiscal" na pasta de testes focado **exclusivamente** em auditar a cobertura entre o `master_file_300_shp` e as traduções do `conversao_completo.json`.

Esse script (chamado `test_completude_json.py`) é ultra-rápido, faz o cruzamento lógico das gigabites de informações em 1 segundo e "dedura" se faltou alguma classe pra ser mapeada, ou se uma classe foi mapeada pela metade (ex: o master shape diz que devia ter 5 atributos, mas a IA só achou 4).
Para chamar o Físcal manualmente e ler o resultado, digite no seu terminal:
`pytest tests/test_completude_json.py -v`

Ele te dirá no relatório final algo como: `100% Passed` (Pode comemorar, nada escapou!) ou apontará as tabelas Shape que "ficaram órfãs".
