# Normalização do Banco de Dados — Livraria CQRS

## 1. Introdução

O projeto Livraria CQRS utiliza dois modelos de persistência de dados, seguindo o padrão arquitetural Command Query Responsibility Segregation (CQRS).

O PostgreSQL é responsável pelas operações de escrita e utiliza um esquema relacional normalizado até a Terceira Forma Normal (3FN). O Neo4j é utilizado para consultas, mantendo uma projeção desnormalizada dos pedidos.

A normalização tem como objetivo reduzir redundâncias, preservar a integridade referencial e evitar anomalias de inserção, atualização e exclusão.

## 2. Modelo inicial — Tabela não normalizada

Inicialmente, podemos representar as vendas da livraria em uma única tabela:

| Pedido | Cliente | Email | Livros | Quantidades | Autor |
|---|---|---|---|---|---|
| 1 | João | joao@email.com | Livro A, Livro B | 1, 2 | Autor X, Autor Y |
| 2 | Maria | maria@email.com | Livro C | 1 | Autor Z |

Esse modelo apresenta problemas porque armazena múltiplos valores em determinadas células e repete informações de clientes, livros e autores.

**Anomalia de inserção:** cadastrar um livro sem que ele tenha sido vendido torna-se difícil se todas as informações estiverem concentradas na tabela de pedidos.

**Anomalia de atualização:** caso um cliente altere seu e-mail, será necessário atualizar todas as linhas que contenham seus pedidos.

**Anomalia de exclusão:** excluir a única venda de determinado livro poderá eliminar também os únicos dados existentes sobre ele.

## 3. Primeira Forma Normal (1FN)

Na Primeira Forma Normal, cada atributo deve armazenar um valor atômico, e cada registro deve ser identificado por uma chave.

A tabela inicial passa a representar os itens individualmente:

| Pedido | Livro | Cliente | Email | Quantidade |
|---|---|---|---|---|
| 1 | Livro A | João | joao@email.com | 1 |
| 1 | Livro B | João | joao@email.com | 2 |
| 2 | Livro C | Maria | maria@email.com | 1 |

Nesse exemplo, a identificação de cada linha pode ser feita pela combinação `(pedido_id, livro_id)`.

A transformação elimina listas de livros e quantidades em uma única célula, mas ainda mantém dados repetidos.

**Anomalia resolvida:** a estrutura passa a permitir a identificação, consulta e atualização individual de cada item do pedido.

**Problema restante:** informações como cliente e e-mail dependem apenas do pedido, enquanto informações próprias do livro dependem apenas do livro. Essas dependências parciais provocam redundância.

## 4. Segunda Forma Normal (2FN)

A Segunda Forma Normal exige que a tabela esteja na 1FN e que os atributos não pertencentes à chave dependam da chave completa, eliminando dependências parciais.

Para isso, separamos os dados em entidades próprias:

**Clientes**

- id
- nome
- email

**Livros**

- id
- titulo
- isbn
- preco

**Pedidos**

- id
- cliente_id
- data_pedido
- status

**Itens do Pedido**

- id
- pedido_id
- livro_id
- quantidade
- preco_unitario

Os relacionamentos são definidos por chaves estrangeiras.

O preço unitário do item corresponde ao valor praticado na venda e não necessariamente ao preço atual do livro.

**Anomalia resolvida:** atualizar o cadastro de um cliente ou o título de um livro não exige modificar todas as linhas dos itens vendidos.

**Problema restante:** atributos que dependem de outras informações não chave podem gerar dependências transitivas, como dados descritivos de autores e categorias armazenados diretamente no cadastro dos livros.

## 5. Terceira Forma Normal (3FN)

A Terceira Forma Normal elimina dependências transitivas indevidas entre atributos não chave.

No modelo final, autores e categorias são entidades independentes e possuem relacionamentos próprios com livros.

O esquema PostgreSQL possui as seguintes tabelas:

| Tabela | Finalidade |
|---|---|
| usuarios | Credenciais de autenticação |
| clientes | Dados cadastrais dos clientes |
| autores | Informações dos autores |
| categorias | Categorias disponíveis |
| livros | Cadastro dos livros |
| livros_autores | Associação entre livros e autores |
| livros_categorias | Associação entre livros e categorias |
| pedidos | Informações gerais dos pedidos |
| itens_pedido | Produtos, quantidades e preços de venda |

A tabela `usuarios` armazena um hash de senha, e não a senha original.

As tabelas associativas possuem chaves compostas para impedir a repetição dos mesmos relacionamentos.

O total financeiro de cada pedido não precisa ser armazenado na tabela `pedidos`, podendo ser calculado pela soma de `quantidade × preco_unitario` dos itens relacionados.

**Anomalia resolvida:** modificar informações de um autor ou de uma categoria exige apenas a atualização do registro correspondente, sem alterar o cadastro de todos os livros associados.

Essa separação também permite cadastrar autores, categorias, clientes e livros independentemente da existência de pedidos.

## 6. Relacionamentos do modelo final

- Um cliente pode realizar vários pedidos.
- Cada pedido pertence a um cliente.
- Um pedido possui um ou mais itens.
- Cada item referencia um livro.
- Um livro pode participar de vários pedidos.
- Um livro pode possuir autores e categorias associados.
- A relação entre livros e autores é representada por `livros_autores`.
- A relação entre livros e categorias é representada por `livros_categorias`.

Esses relacionamentos são implementados no PostgreSQL utilizando chaves primárias, chaves estrangeiras e restrições de unicidade.

## 7. Modelo desnormalizado de leitura

Para atender à arquitetura CQRS, o Neo4j mantém nós identificados pelo rótulo `PedidoResumo`.

Cada resumo possui os dados necessários para consultar o pedido sem executar junções no PostgreSQL, incluindo:

- Identificador do pedido.
- Identificador e nome do cliente.
- E-mail do cliente.
- Data do pedido.
- Status.
- Total calculado.
- Quantidade de itens.
- Lista de itens serializada em JSON.

Essa estrutura apresenta redundância intencional, pois algumas informações do cliente e dos livros são reproduzidas para facilitar a leitura.

A desnormalização é adequada nesse contexto porque o PostgreSQL permanece como fonte principal das informações.

## 8. Sincronização e deduplicação

A atualização do banco de leitura é realizada pelo endpoint `POST /sincronizar`.

O serviço consulta os dados normalizados do PostgreSQL, constrói os resumos e executa operações `MERGE` no Neo4j.

A propriedade `pedido_id` possui uma restrição de unicidade, impedindo a criação de mais de um resumo para o mesmo pedido.

Na validação realizada durante o desenvolvimento, o Neo4j apresentou:

| Métrica | Resultado |
|---|---:|
| Registros de pedidos | 2.002 |
| Identificadores únicos | 2.002 |
| Registros duplicados | 0 |

Esses resultados demonstram a ausência de duplicação no conjunto consultado. A comprovação da idempotência requer ainda registrar duas execuções consecutivas da sincronização, sem alteração na contagem.

## 9. Conclusão

A aplicação das formas normais permitiu separar as responsabilidades de cada entidade, reduzir redundâncias e estabelecer relacionamentos consistentes.

O PostgreSQL mantém a integridade dos dados utilizados nas operações de escrita, enquanto o Neo4j disponibiliza um modelo de leitura desnormalizado.

Essa organização representa a aplicação prática do padrão CQRS, com separação de responsabilidades, sincronização e prevenção de duplicações.