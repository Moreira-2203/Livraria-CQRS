# Livraria CQRS — PostgreSQL, Neo4j e FastAPI

## 1. Apresentação

Este projeto implementa uma API de gerenciamento de pedidos de uma livraria utilizando o padrão arquitetural **CQRS (Command Query Responsibility Segregation)**.

A proposta consiste em separar as operações de escrita das operações de leitura, utilizando modelos de dados diferentes para cada responsabilidade.

O sistema utiliza PostgreSQL como banco de escrita, com modelagem relacional normalizada até a Terceira Forma Normal (3FN), e Neo4j como banco de leitura, com projeções desnormalizadas.

O backend foi desenvolvido em Python com FastAPI, incluindo autenticação JWT, armazenamento de senhas por hash, proteção de rotas e sincronização idempotente.

## 2. Tecnologias utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python | Linguagem de programação |
| FastAPI | Desenvolvimento da API REST |
| PostgreSQL | Banco de escrita normalizado |
| Neo4j | Banco de leitura desnormalizado |
| Psycopg | Comunicação com PostgreSQL |
| Neo4j Python Driver | Comunicação com Neo4j |
| PyJWT | Autenticação com tokens JWT |
| pwdlib / Argon2 | Hash seguro de senhas |
| python-dotenv | Carregamento de variáveis de ambiente |
| Uvicorn | Servidor de desenvolvimento |
| Swagger UI | Testes das rotas HTTP |

## 3. Arquitetura CQRS

A aplicação separa as operações em três responsabilidades principais.

**Escrita — PostgreSQL**

Os dados são armazenados em tabelas relacionadas, organizadas até a Terceira Forma Normal.

A rota `POST /pedidos` permite cadastrar novos pedidos utilizando autenticação JWT.

**Integração — Serviço Python**

A rota `POST /sincronizar` consulta os dados do PostgreSQL, reúne as informações dos pedidos e atualiza o modelo de leitura no Neo4j.

A integração utiliza `MERGE` e restrição de unicidade para evitar duplicações.

**Leitura — Neo4j**

A rota `GET /relatorios/pedidos` consulta os nós `PedidoResumo`.

Cada resumo contém informações do cliente, pedido, livros, quantidades e valores, evitando a necessidade de executar JOINs no momento da leitura.

### Fluxo

```text
CLIENTE / SWAGGER
       |
       v
   FASTAPI
       |
       +----> AUTENTICACAO JWT
       |
       +----> POST /pedidos
       |           |
       |           v
       |       POSTGRESQL
       |       (ESCRITA 3FN)
       |           |
       |           v
       |     POST /sincronizar
       |           |
       |           v
       |         NEO4J
       |     (LEITURA CQRS)
       |           |
       +----> GET /relatorios/pedidos
```

## 4. Modelo de dados

O PostgreSQL contém nove tabelas:

1. `usuarios`
2. `clientes`
3. `autores`
4. `categorias`
5. `livros`
6. `livros_autores`
7. `livros_categorias`
8. `pedidos`
9. `itens_pedido`

Os relacionamentos são implementados com chaves primárias, chaves estrangeiras e restrições de unicidade.

A evolução da modelagem 1FN → 2FN → 3FN está documentada em `docs/normalizacao.md`.

O Neo4j contém a projeção desnormalizada `PedidoResumo`, identificada pela propriedade `pedido_id`.

## 5. Requisitos para execução

Para executar o projeto, é necessário possuir:

- Python 3.10 ou superior.
- PostgreSQL instalado e em execução.
- Neo4j Desktop ou instância Neo4j compatível.
- VS Code ou outro editor de código.
- Acesso ao terminal PowerShell no Windows.

## 6. Instalação

Clone o repositório:

```bash
git clone URL_DO_REPOSITORIO
```

Acesse a pasta do projeto:

```bash
cd livraria_cqrs
```

Crie o ambiente virtual:

```powershell
py -m venv .venv
```

Ative o ambiente no Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

## 7. Configuração das variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto a partir do `.env.example`.

Configure as variáveis:

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=livraria_cqrs
POSTGRES_USER=postgres
POSTGRES_PASSWORD=SENHA_DO_POSTGRESQL

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=SENHA_DO_NEO4J
NEO4J_DATABASE=neo4j

JWT_SECRET=CHAVE_ALEATORIA_SEGURA
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

A URI do Neo4j pode variar conforme a configuração da instância.

Uma chave JWT pode ser gerada utilizando:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**Importante:** o arquivo `.env` contém informações sigilosas e não deve ser enviado ao GitHub.

## 8. Configuração dos bancos

### PostgreSQL

Crie um banco denominado `livraria_cqrs`.

Execute o arquivo:

`sql/criar_banco.sql`

Esse script cria as nove tabelas e suas restrições.

Ele deve ser executado em um banco novo e vazio.

### Neo4j

Inicie a instância Neo4j e confirme que a aplicação consegue estabelecer conexão.

O modelo de leitura `PedidoResumo` e sua restrição de unicidade são preparados pelo serviço de sincronização.

### Dados iniciais

O projeto reaproveita os dados da atividade anterior da livraria desenvolvida no Neo4j.

Para executar a migração inicial, com o Neo4j de origem contendo esses dados, utilize:

```powershell
python scripts/importar_neo4j.py
```

Essa etapa é necessária somente para reproduzir a base inicial a partir do banco Neo4j anterior. O arquivo de migração não gera sozinho os dados de exemplo.

## 9. Testar as conexões

Execute:

```powershell
python app/database/testar_conexoes.py
```

O programa verifica as conexões PostgreSQL e Neo4j e apresenta os resultados no terminal.

## 10. Criar usuário

Execute:

```powershell
python scripts/criar_usuario.py
```

Informe um nome de usuário e uma senha com pelo menos 12 caracteres.

A senha é protegida por hash antes de ser gravada no PostgreSQL.

## 11. Iniciar a API

No terminal, execute:

```powershell
python -m uvicorn app.main:app --reload
```

A documentação interativa estará disponível em:

http://127.0.0.1:8000/docs

## 12. Rotas disponíveis

| Método | Rota | Finalidade | JWT |
|---|---|---|---|
| GET | `/` | Verificar funcionamento da API | Não |
| POST | `/login` | Autenticar e obter token | Não |
| GET | `/perfil` | Consultar usuário autenticado | Sim |
| POST | `/pedidos` | Cadastrar pedido no PostgreSQL | Sim |
| POST | `/sincronizar` | Atualizar resumos no Neo4j | Sim |
| GET | `/relatorios/pedidos` | Consultar dados desnormalizados | Sim |

### Exemplo de login

**POST /login**

```json
{
  "usuario": "USUARIO_CADASTRADO",
  "senha": "SENHA_CADASTRADA"
}
```

Quando as credenciais são válidas, a API devolve um token JWT.

### Exemplo de criação de pedido

**POST /pedidos**

```json
{
  "cliente_id": 1,
  "itens": [
    {
      "livro_id": 1,
      "quantidade": 2
    },
    {
      "livro_id": 2,
      "quantidade": 1
    }
  ]
}
```

O pedido é gravado no PostgreSQL com seus respectivos itens.

### Exemplo de sincronização

**POST /sincronizar**

O endpoint consulta os pedidos no PostgreSQL e cria ou atualiza os resumos no Neo4j.

### Exemplo de leitura

**GET /relatorios/pedidos?limite=5**

Retorna até cinco pedidos, ordenados pelo identificador, com informações do cliente, livros e valores.

## 13. Segurança

O projeto implementa as seguintes medidas:

- Senhas armazenadas utilizando hash seguro.
- Autenticação com JWT.
- Proteção de rotas de escrita.
- Proteção da rota de leitura.
- Retorno HTTP 401 para requisições não autorizadas.
- Consultas SQL parametrizadas.
- Credenciais armazenadas em variáveis de ambiente.
- Arquivo `.env` excluído do versionamento por `.gitignore`.
- Respostas sem exposição de senhas e credenciais.

## 14. Resultados dos testes

Durante o desenvolvimento, foram realizados testes pelo Swagger, PostgreSQL e Neo4j.

| Teste | Resultado observado |
|---|---|
| Conexão PostgreSQL | Sucesso |
| Conexão Neo4j | Sucesso |
| Login com credenciais inválidas | HTTP 401 |
| Perfil sem token | HTTP 401 |
| Perfil com token válido | HTTP 200 |
| Criação de pedido autenticada | HTTP 201 |
| Criação de pedido sem token | HTTP 401 |
| Sincronização PostgreSQL → Neo4j | HTTP 200 |
| Consulta de relatórios | HTTP 200 |
| Pedidos únicos no Neo4j | 2.002 |
| Pedidos duplicados no Neo4j | 0 |

A ausência de duplicação foi confirmada pela consulta Cypher que compara a quantidade total de nós `PedidoResumo` com a quantidade de identificadores distintos.

## 15. Documentação complementar

- `docs/normalizacao.md`: explicação da normalização e anomalias resolvidas.
- `docs/declaracao_ia.md`: declaração de uso de inteligência artificial e métricas de validação.
- `docs/autoavaliacao.md`: autoavaliação e tempo gasto.
- `sql/consultas_teste.sql`: consultas utilizadas para verificar o banco.
- `docs/evidencias/`: capturas dos testes realizados.

## 16. Conclusão

O projeto demonstra a aplicação prática do padrão CQRS por meio da separação entre operações de escrita e leitura.

O PostgreSQL é responsável pela integridade e organização dos dados, enquanto o Neo4j oferece uma estrutura desnormalizada para consultas.

A integração entre os dois bancos utiliza identificadores únicos e operações de atualização que evitam duplicações.

A API FastAPI disponibiliza autenticação JWT, rotas protegidas e documentação interativa pelo Swagger.