
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Localiza o .env na raiz do projeto
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def testar_postgresql():
    print("\nTestando PostgreSQL...")

    try:
        with psycopg.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT current_database()")
                banco = cursor.fetchone()[0]

                print(f"PostgreSQL conectado: {banco}")
                return True

    except Exception as erro:
        print(f"Erro no PostgreSQL: {erro}")
        return False


def testar_neo4j():
    print("\nTestando Neo4j...")

    try:
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
                resultado = session.run(
                    "MATCH (n) RETURN count(n) AS total"
                ).single()

                print("Neo4j conectado!")
                print(f"Total de nos: {resultado['total']}")
                return True

    except Exception as erro:
        print(f"Erro no Neo4j: {erro}")
        return False


if __name__ == "__main__":
    postgres_ok = testar_postgresql()
    neo4j_ok = testar_neo4j()

    if postgres_ok and neo4j_ok:
        print("\nAmbos os bancos estao conectados!")
    else:
        print("\nVerifique as conexoes com erro.")
