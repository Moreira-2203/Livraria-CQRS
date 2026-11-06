
import json
import os
from decimal import Decimal

import psycopg
from psycopg.rows import dict_row
from neo4j import GraphDatabase
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def conectar_postgres():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )


def buscar_pedidos():
    consulta = """
        SELECT
            p.id AS pedido_id,
            p.data_pedido,
            p.status,
            c.id AS cliente_id,
            c.nome AS cliente_nome,
            c.email AS cliente_email,
            i.livro_id,
            l.titulo AS livro_titulo,
            i.quantidade,
            i.preco_unitario
        FROM pedidos p
        JOIN clientes c ON c.id = p.cliente_id
        JOIN itens_pedido i ON i.pedido_id = p.id
        JOIN livros l ON l.id = i.livro_id
        ORDER BY p.id, i.id
    """

    with conectar_postgres() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(consulta)
            registros = cur.fetchall()

    pedidos = {}

    for r in registros:
        pid = r["pedido_id"]

        if pid not in pedidos:
            pedidos[pid] = {
                "pedido_id": pid,
                "cliente_id": r["cliente_id"],
                "cliente_nome": r["cliente_nome"],
                "cliente_email": r["cliente_email"],
                "data_pedido": r["data_pedido"].isoformat(),
                "status": r["status"],
                "total": Decimal("0.00"),
                "itens": []
            }

        subtotal = (
            r["preco_unitario"] * r["quantidade"]
        )

        pedidos[pid]["itens"].append({
            "livro_id": r["livro_id"],
            "titulo": r["livro_titulo"],
            "quantidade": r["quantidade"],
            "preco_unitario": float(r["preco_unitario"]),
            "subtotal": float(subtotal)
        })

        pedidos[pid]["total"] += subtotal

    resultado = []

    for pedido in pedidos.values():
        resultado.append({
            "pedido_id": pedido["pedido_id"],
            "cliente_id": pedido["cliente_id"],
            "cliente_nome": pedido["cliente_nome"],
            "cliente_email": pedido["cliente_email"],
            "data_pedido": pedido["data_pedido"],
            "status": pedido["status"],
            "total": float(pedido["total"]),
            "quantidade_itens": len(pedido["itens"]),
            "itens_json": json.dumps(
                pedido["itens"],
                ensure_ascii=False
            )
        })

    return resultado


def sincronizar_pedidos():
    pedidos = buscar_pedidos()

    consulta = """
        UNWIND $lote AS p

        MERGE (r:PedidoResumo {pedido_id: p.pedido_id})

        SET
            r.cliente_id = p.cliente_id,
            r.cliente_nome = p.cliente_nome,
            r.cliente_email = p.cliente_email,
            r.data_pedido = p.data_pedido,
            r.status = p.status,
            r.total = p.total,
            r.quantidade_itens = p.quantidade_itens,
            r.itens_json = p.itens_json
    """

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

            # Impede dois resumos com mesmo pedido_id
            session.run("""
                CREATE CONSTRAINT pedido_resumo_unico
                IF NOT EXISTS
                FOR (r:PedidoResumo)
                REQUIRE r.pedido_id IS UNIQUE
            """).consume()

            tamanho_lote = 200

            for inicio in range(0, len(pedidos), tamanho_lote):
                lote = pedidos[
                    inicio:inicio + tamanho_lote
                ]

                session.run(
                    consulta,
                    lote=lote
                ).consume()

            resultado = session.run("""
                MATCH (r:PedidoResumo)
                RETURN count(r) AS total
            """).single()

            total_neo4j = resultado["total"]

    return {
        "mensagem": "Sincronizacao concluida",
        "pedidos_processados": len(pedidos),
        "total_resumos_neo4j": total_neo4j
    }


def consultar_resumos(limite=20):
    with GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(
            os.getenv("NEO4J_USER"),
            os.getenv("NEO4J_PASSWORD")
        )
    ) as driver:

        with driver.session(
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        ) as session:

            resultado = session.run("""
                MATCH (r:PedidoResumo)
                RETURN
                    r.pedido_id AS pedido_id,
                    r.cliente_nome AS cliente,
                    r.status AS status,
                    r.total AS total,
                    r.data_pedido AS data_pedido,
                    r.itens_json AS itens_json
                ORDER BY pedido_id DESC
                LIMIT $limite
            """, limite=limite)

            registros = [dict(r) for r in resultado]

    for r in registros:
        r["itens"] = json.loads(r.pop("itens_json"))

    return registros
