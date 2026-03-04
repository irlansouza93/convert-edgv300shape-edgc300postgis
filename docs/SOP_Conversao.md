# Standard Operating Procedure (SOP) - Conversão de Shapefiles para PostGIS EDGV

Este documento serve como guia definitivo para garantir que novos projetos de conversão de dados geoespaciais (Shapefile -> PostGIS) ocorram de forma padronizada e imune a perdas silenciosas de atributos e domínios.

## 1. Mapeamento de Colunas (Fuzzy Match vs Manual)
O script automatizado tentará criar vínculos (matches) entre as colunas do seu Shapefile e os Atributos exigidos pelo BD PostgreSQL através do arquivo `master_file_...json`.
* **Risco Silencioso:** Se a sigla no Shapefile for muito diferente da palavra completa na EDGV (Ex: `FINPAT` -> `finalidadepatio`), o conversor **descartará a coluna inteira**, não levando em consideração suas traduções.
* **SOP Regra 1:** Sempre que introduzir um novo banco de dados no futuro, abra o arquivo `scripts/autofill_conversao.py` e adicione qualquer par de equivalência estranha diretamente no bloco de dicionário interno chamado `overrides`.
Exemplo:
```python
    overrides = {
        'situaespac': 'situacaoespacial',
        'finpat': 'finalidadepatio'
    }
```

## 2. Injeção Global de Traduções (A Regra de Ouro)
Na EDGV existem inúmeras listas de Domínios. O motor foi reescrito para priorizar a inteligência manual do analista.

* **SOP Regra 2:** Quando quiser forçar o motor a traduzir um atributo (ex: `TIPOEDIF` recebendo os Códigos Numéricos 03, 05, etc.), declare esse dicionário de domínios na lista solta e principal `mapeamento_atributos` direto no **final** ou na **raiz** do arquivo json de referência `conversao_pg-edgv..._shp-edgv...json`. 
Deixe ele lá, independente de classes. Quando o motor for fabricar o arquivo SQL final, ele varrerá todas as classes do Brasil que existirem; se alguma delas possuir a coluna Shape "TIPOEDIF", ele herdará as traduções da raiz universalmente, imune a erros de hierarquia!

## 3. Obrigatoriedades Geográficas ("Desconhecido" vs NULL)
* **SOP Regra 3:** Não assuma que todos os campos do FME preencherão "9999" por padrão. O conversor agora só força texto "Desconhecido" (ou inteiro 9999) **SE** a modelagem PostGIS exigir cardinalidade _1..1_ (NOT NULL). Para não poluir o banco atoa, colunas 0..1 recebem `NULL`.

## 4. O Sistema de Auditoria (Sempre Verifique)
Nunca conclua o push para produção sem olhar a "Caixa Preta".

* **SOP Regra 4:** O motor escreve o arquivo `relatorio_inconsistencias.csv` a cada execução. Esse relatório contém:
`Classe, ID Original, Coluna, Motivo`
Foque em caçar todas as linhas cujo Motivo seja `Obrigatório (Vazio/Inexistente no SHP)`. Isso denuncia onde o seu shapefile está vazio e a conversão precisou forçar um `9999`. É seu painel de controle para voltar ao QGIS e desenhar a informação faltante se necessário, antes do SQL Final.
