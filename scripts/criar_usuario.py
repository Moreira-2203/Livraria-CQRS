
import os
import sys
from getpass import getpass
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from pwdlib import PasswordHash

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

usuario = input("Nome do usuario: ").strip()
senha = getpass("Senha: ")

if not usuario or len(senha) < 12:
    sys.exit("Informe um usuario e uma senha de pelo menos 12 caracteres.")

hash_senha = PasswordHash.recommended().hash(senha)

with psycopg.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT", "5432"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
) as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO usuarios (nome_usuario, senha_hash)
            VALUES (%s, %s)
            ON CONFLICT (nome_usuario)
            DO UPDATE SET senha_hash = EXCLUDED.senha_hash
            """,
            (usuario, hash_senha)
        )

print("Usuario cadastrado com sucesso!")
