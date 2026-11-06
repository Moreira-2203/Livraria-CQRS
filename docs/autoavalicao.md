# Autoavaliação de Entendimento, Domínio e Tempo Gasto

**Projeto:** Livraria Online — Arquitetura CQRS

## 1. Tabela de autoavaliação

| Parte do exercício | Nota (1–5) | Justificativa | Tempo aproximado |
|---|---|---|---|
| Modelagem do banco de escrita até 3FN | 4 | Compreendi a separação das entidades e a utilização de chaves primárias e estrangeiras. A modelagem foi aplicada e validada no PostgreSQL, com auxílio na elaboração da documentação das formas normais. | 1h30 |
| Banco de leitura desnormalizado e deduplicação | 4 | Compreendi a criação de uma estrutura voltada para consultas no Neo4j. Verifiquei a presença de 2.002 identificadores únicos e nenhum registro duplicado. | 1h |
| Serviço de integração | 4 | Implementei e testei a sincronização entre PostgreSQL e Neo4j, utilizando operações MERGE para atualizar os registros. Ainda considero importante aprofundar meus conhecimentos sobre sincronização automática e tratamento de falhas. | 1h30 |
| Autenticação (login/token) | 4 | Consegui implementar e testar autenticação JWT e armazenamento de senhas com hash. Verifiquei os retornos HTTP 200 e 401 nas rotas protegidas. | 1h |
| Segurança (env, hash, queries parametrizadas) | 4 | Apliquei variáveis de ambiente, hash de senhas e consultas SQL parametrizadas. Compreendi a importância desses recursos, embora ainda precise aprofundar conhecimentos sobre segurança em aplicações reais. | 1h |

## 2. Tempo total aproximado

**Total estimado: 6 horas.**

Os tempos apresentados representam uma estimativa das atividades de configuração, implementação, testes e correções, não uma medição cronológica precisa.

## 3. Justificativa geral

O desenvolvimento do projeto permitiu compreender a separação entre operações de escrita e leitura utilizando a arquitetura CQRS.

Durante a atividade, trabalhei com PostgreSQL, Neo4j, Python e FastAPI, realizando a integração entre dois bancos de dados com estruturas diferentes.

Consegui implementar autenticação JWT, proteger rotas, cadastrar pedidos e consultar informações desnormalizadas.

As dificuldades encontradas durante a configuração dos bancos e a implementação dos recursos foram resolvidas por meio de testes, pesquisas e orientação de ferramentas auxiliares.

Atribuí nota 4 às etapas porque considero que consegui compreender e aplicar os principais conceitos, mas ainda necessito de consultas à documentação e apoio para desenvolver soluções semelhantes de forma totalmente independente.

## 4. Considerações finais

O exercício contribuiu para ampliar meus conhecimentos sobre modelagem relacional, bancos de dados orientados a grafos, autenticação e desenvolvimento de APIs.

A aplicação prática dos conceitos demonstrou como a normalização preserva a integridade dos dados e como a desnormalização pode facilitar operações de leitura.

O projeto também permitiu compreender a importância da prevenção de duplicações em serviços de integração.