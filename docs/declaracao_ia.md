# Declaração de Uso de Inteligência Artificial

## 1. Ferramentas utilizadas

Durante o desenvolvimento do projeto Livraria CQRS, foi utilizado o ChatGPT, da OpenAI, como ferramenta auxiliar de orientação, explicação técnica, geração de exemplos de código, organização da arquitetura e apoio à documentação.

## 2. Partes desenvolvidas com auxílio de IA

A inteligência artificial foi utilizada como apoio nas seguintes atividades:

- Planejamento da arquitetura CQRS.
- Modelagem relacional até a Terceira Forma Normal.
- Criação e adaptação dos scripts PostgreSQL.
- Elaboração do script de importação dos dados existentes no Neo4j.
- Implementação da autenticação JWT.
- Aplicação de hash às senhas.
- Desenvolvimento das rotas protegidas do FastAPI.
- Implementação da sincronização PostgreSQL → Neo4j.
- Utilização de `MERGE` e restrição de unicidade para deduplicação.
- Elaboração de consultas e procedimentos de teste.
- Organização da documentação técnica.

## 3. Validação quantitativa

As sugestões foram verificadas por meio da execução dos programas e consultas nos ambientes utilizados.

| Métrica | Resultado |
|---|---|
| Conexões de bancos testadas com sucesso | 2 |
| Tabelas criadas no PostgreSQL | 9 |
| Clientes importados | 1.001 |
| Livros importados | 500 |
| Pedidos importados inicialmente | 2.001 |
| Itens de pedidos importados | 5.002 |
| Pedidos presentes após os testes de cadastro | 2.002 |
| Resumos registrados no Neo4j | 2.002 |
| Identificadores distintos | 2.002 |
| Duplicações identificadas | 0 |
| Rota protegida sem token | HTTP 401 |
| Cadastro autenticado de pedido | HTTP 201 |
| Consulta desnormalizada | HTTP 200 |

Essas métricas foram obtidas por meio de execuções no VS Code, respostas HTTP do Swagger, consultas SQL e consultas Cypher.

## 4. Validação qualitativa

A validação não se limitou à geração automática de código.

Foram realizados testes no ambiente de execução, observando se os comandos produziam os resultados esperados.

O funcionamento da autenticação foi verificado por meio de requisições com e sem token.

A integridade dos dados foi examinada utilizando consultas com relacionamentos entre pedidos, clientes, livros e itens.

A sincronização foi validada pela presença dos dados no Neo4j e pela ausência de identificadores duplicados.

Os erros e dificuldades encontrados durante a configuração do ambiente foram analisados e corrigidos ao longo do desenvolvimento.

## 5. Limitações e verificações pendentes

A consulta de unicidade confirmou ausência de duplicações no modelo de leitura. O teste formal de idempotência deve apresentar duas execuções consecutivas de sincronização, demonstrando que a segunda execução mantém a mesma quantidade de registros.

Os testes documentados concentram-se nos cenários funcionais realizados. Não constituem uma auditoria completa de segurança nem um teste de carga.

## 6. Conclusão

A IA foi utilizada como ferramenta de apoio ao desenvolvimento, enquanto a execução, configuração dos ambientes, verificação dos resultados e validação funcional ocorreram por meio das ferramentas de programação e bancos de dados.

A utilização da ferramenta contribuiu para a construção e compreensão do projeto, sendo as sugestões submetidas a testes práticos antes de serem consideradas funcionais.