# Regras de Desenvolvimento do Projeto

Ao desenvolver este projeto, as seguintes práticas e diretrizes devem ser seguidas rigorosamente:

1. **Código Limpo (Clean Code):** Garantir legibilidade, simplicidade e consistência. Nomes de variáveis, métodos e classes devem ser claros e em inglês (para manter padrão internacional, embora logs e documentações possam ser em português caso acordado).
2. **Arquitetura de Software:** Utilizar Padrões Arquiteturais como Hexagonal/Clean Architecture, separando claramente o domínio (regras de conversão), a infraestrutura (leitura de shapefiles, escrita de .sql) e a interface (CLI para execução).
3. **Organização Modular:**
    - `src/domain/`: Regras de negócio, entidades e interfaces.
    - `src/infrastructure/`: Implementação de leitura de shapefiles (ex: `geopandas`, `fiona`) e geração de arquivos SQL.
    - `src/application/`: Casos de uso e orquestração.
4. **Testes Automatizados:** Escrever testes unitários e de integração (usando `pytest`) para assegurar confiabilidade e facilitar a manutenção.
5. **Documentação:** O código e APIs devem ser documentados de forma clara (Docstrings). Comentários só devem ser adicionados quando o "porquê" de algo for complexo e o código por si só não for auto-explicativo.
6. **Evitar Duplicação (DRY):** Preferir abstrações bem definidas e reutilizáveis (SOLID).
7. **Escalabilidade, Manutenibilidade e Extensibilidade:** O código deve lidar com grandes volumes de dados de forma eficiente (processando arquivos sequencialmente ou em blocos, sem carregar tudo na memória se os dados forem imensos).
8. **Segurança e Versionamento:** Manipulação segura de caminhos e validação de inputs.
9. **Convenções e Guias de Estilo:** Seguir o padrão PEP 8 aplicável ao Python.
10. **Clareza e Qualidade:** Priorizar sempre a simplicidade funcional sobre a complexidade prematura.
