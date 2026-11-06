
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

# ============================================
# CONFIGURACAO
# ============================================

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def buscar_neo4j(session, consulta):
    resultado = session.run(consulta)
    return [dict(registro) for registro in resultado]


def extrair_dados():
    print("\nConectando ao Neo4j...")

    consultas = {
        "clientes": """
            MATCH (c:Cliente)
            RETURN properties(c) AS dados
        """,

        "autores": """
            MATCH (a:Autor)
            RETURN properties(a) AS dados
        """,

        "categorias": """
            MATCH (c:Categoria)
            RETURN properties(c) AS dados
        """,

        "livros": """
            MATCH (l:Livro)
            RETURN properties(l) AS dados
        """,

        "livros_autores": """
            MATCH (l:Livro)-[:ESCRITO_POR]->(a:Autor)
            RETURN l.id AS livro_id, a.id AS autor_id
        """,

        "livros_categorias": """
            MATCH (l:Livro)-[:PERTENCE_A]->(c:Categoria)
            RETURN l.id AS livro_id, c.id AS categoria_id
        """,

        "pedidos": """
            MATCH (p:Pedido)-[:FEITO_POR]->(c:Cliente)
            RETURN properties(p) AS dados,
                   c.id AS cliente_id
        """,

        "itens": """
            MATCH (p:Pedido)-[r:CONTEM]->(l:Livro)
            RETURN p.id AS pedido_id,
                   l.id AS livro_id,
                   r.quantidade AS quantidade,
                   r.preco_unitario AS preco_unitario
        """
    }

    dados = {}

    with GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(
            os.getenv("NEO4J_USER"),
            os.getenv("NEO4J_PASSWORD")
        )
    ) as driver:

        driver.verify_connectivity()

        with driver.session(
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        ) as session:

            for nome, consulta in consultas.items():
                dados[nome] = buscar_neo4j(session, consulta)
                print(f"{nome}: {len(dados[nome])} registros")

    return dados


# ============================================
# IMPORTACAO PARA POSTGRESQL
# ============================================

def importar_postgresql(dados):
    print("\nConectando ao PostgreSQL...")

    with psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    ) as conn:

        with conn.cursor() as cur:

            # 1. CLIENTES
            print("\nImportando clientes...")

            for registro in dados["clientes"]:
                c = registro["dados"]

                cur.execute("""
                    INSERT INTO clientes
                    (id, nome, email, cidade, estado, membro_desde)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        email = EXCLUDED.email,
                        cidade = EXCLUDED.cidade,
                        estado = EXCLUDED.estado,
                        membro_desde = EXCLUDED.membro_desde
                """, (
                    c["id"],
                    c["nome"],
                    c.get("email"),
                    c.get("cidade"),
                    c.get("estado"),
                    c.get("membro_desde")
                ))

            # 2. AUTORES
            print("Importando autores...")

            for registro in dados["autores"]:
                a = registro["dados"]

                cur.execute("""
                    INSERT INTO autores
                    (id, nome, nacionalidade, ano_nascimento)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        nacionalidade = EXCLUDED.nacionalidade,
                        ano_nascimento = EXCLUDED.ano_nascimento
                """, (
                    a["id"],
                    a["nome"],
                    a.get("nacionalidade"),
                    a.get("ano_nascimento")
                ))

            # 3. CATEGORIAS
            print("Importando categorias...")

            for registro in dados["categorias"]:
                c = registro["dados"]

                cur.execute("""
                    INSERT INTO categorias
                    (id, nome, descricao)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        nome = EXCLUDED.nome,
                        descricao = EXCLUDED.descricao
                """, (
                    c["id"],
                    c["nome"],
                    c.get("descricao")
                ))

            # 4. LIVROS
            print("Importando livros...")

            for registro in dados["livros"]:
                l = registro["dados"]

                cur.execute("""
                    INSERT INTO livros
                    (id, titulo, isbn, preco, estoque,
                     ano_publicacao, avaliacao_media)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        titulo = EXCLUDED.titulo,
                        isbn = EXCLUDED.isbn,
                        preco = EXCLUDED.preco,
                        ano_publicacao = EXCLUDED.ano_publicacao,
                        avaliacao_media = EXCLUDED.avaliacao_media
                """, (
                    l["id"],
                    l["titulo"],
                    l.get("isbn"),
                    l["preco"],
                    0,
                    l.get("ano_publicacao"),
                    l.get("avaliacao_media")
                ))

            # 5. LIVROS - AUTORES
            print("Importando relacoes livro-autor...")

            for r in dados["livros_autores"]:
                cur.execute("""
                    INSERT INTO livros_autores
                    (livro_id, autor_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    r["livro_id"],
                    r["autor_id"]
                ))

            # 6. LIVROS - CATEGORIAS
            print("Importando relacoes livro-categoria...")

            for r in dados["livros_categorias"]:
                cur.execute("""
                    INSERT INTO livros_categorias
                    (livro_id, categoria_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    r["livro_id"],
                    r["categoria_id"]
                ))

            # 7. PEDIDOS
            print("Importando pedidos...")

            for registro in dados["pedidos"]:
                p = registro["dados"]

                cur.execute("""
                    INSERT INTO pedidos
                    (id, cliente_id, data_pedido, status)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        cliente_id = EXCLUDED.cliente_id,
                        data_pedido = EXCLUDED.data_pedido,
                        status = EXCLUDED.status
                """, (
                    p["id"],
                    registro["cliente_id"],
                    p["data_pedido"],
                    p["status"]
                ))

            # 8. ITENS DOS PEDIDOS
            print("Importando itens dos pedidos...")

            for r in dados["itens"]:
                cur.execute("""
                    INSERT INTO itens_pedido
                    (pedido_id, livro_id, quantidade, preco_unitario)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (pedido_id, livro_id)
                    DO UPDATE SET
                        quantidade = EXCLUDED.quantidade,
                        preco_unitario = EXCLUDED.preco_unitario
                """, (
                    r["pedido_id"],
                    r["livro_id"],
                    r["quantidade"],
                    r["preco_unitario"]
                ))

            # 9. AJUSTAR SEQUENCIAS DOS IDS
            print("Ajustando sequencias...")

            tabelas = [
                "clientes",
                "autores",
                "categorias",
                "livros",
                "pedidos",
                "itens_pedido"
            ]

            for tabela in tabelas:
                cur.execute(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{tabela}', 'id'),
                        COALESCE(MAX(id), 1),
                        MAX(id) IS NOT NULL
                    )
                    FROM {tabela}
                """)

            # Verifica a quantidade de registros
            print("\nRESULTADO DA IMPORTACAO")

            for tabela in tabelas:
                cur.execute(f"SELECT COUNT(*) FROM {tabela}")
                quantidade = cur.fetchone()[0]
                print(f"{tabela}: {quantidade}")

        # Commit automatico se nao ocorrer erro.
        # Em caso de excecao, rollback automatico.

    print("\nIMPORTACAO CONCLUIDA COM SUCESSO!")


# ============================================
# EXECUCAO
# ============================================

if __name__ == "__main__":
    try:
        print("=" * 45)
        print("LIVRARIA CQRS - IMPORTACAO INICIAL")
        print("=" * 45)

        dados = extrair_dados()
        importar_postgresql(dados)

    except Exception as erro:
        print(f"\nERRO NA IMPORTACAO: {erro}")
        print("Verifique a mensagem acima.")
        raise
