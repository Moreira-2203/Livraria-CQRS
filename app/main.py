
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import psycopg

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from pwdlib import PasswordHash

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

app = FastAPI(
    title="Livraria CQRS",
    description="API com PostgreSQL e Neo4j",
    version="1.0.0"
)

security = HTTPBearer(auto_error=False)
password_hash = PasswordHash.recommended()

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(
    os.getenv("JWT_EXPIRE_MINUTES", "60")
)


def conectar_postgres():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )


class LoginRequest(BaseModel):
    usuario: str
    senha: str


@app.get("/")
def inicio():
    return {
        "projeto": "Livraria CQRS",
        "status": "API funcionando"
    }


@app.post("/login")
def login(dados: LoginRequest):
    with conectar_postgres() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, nome_usuario, senha_hash
                FROM usuarios
                WHERE nome_usuario = %s
                """,
                (dados.usuario,)
            )
            usuario = cur.fetchone()

    if (
        not usuario
        or not password_hash.verify(
            dados.senha, usuario[2]
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Usuario ou senha invalidos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=JWT_EXPIRE_MINUTES
    )

    token = jwt.encode(
        {
            "sub": str(usuario[0]),
            "exp": expiracao
        },
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


def usuario_autenticado(
    credenciais: HTTPAuthorizationCredentials = Depends(security)
):
    if (
        credenciais is None
        or credenciais.scheme.lower() != "bearer"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token obrigatorio",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(
            credenciais.credentials,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        usuario_id = int(payload["sub"])

    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Token invalido ou expirado",
            headers={"WWW-Authenticate": "Bearer"}
        )

    with conectar_postgres() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, nome_usuario
                FROM usuarios
                WHERE id = %s
                """,
                (usuario_id,)
            )
            usuario = cur.fetchone()

    if usuario is None:
        raise HTTPException(
            status_code=401,
            detail="Usuario nao encontrado"
        )

    return {
        "id": usuario[0],
        "nome_usuario": usuario[1]
    }


@app.get("/perfil")
def perfil(usuario=Depends(usuario_autenticado)):
    return {
        "mensagem": "Acesso autorizado",
        "usuario": usuario
    }


# ============================================
# CQRS - ROTAS DE ESCRITA
# ============================================

from decimal import Decimal
from pydantic import Field


class ItemPedidoRequest(BaseModel):
    livro_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)


class CriarPedidoRequest(BaseModel):
    cliente_id: int = Field(gt=0)
    itens: list[ItemPedidoRequest] = Field(min_length=1)


@app.post("/pedidos", status_code=201)
def criar_pedido(
    dados: CriarPedidoRequest,
    usuario=Depends(usuario_autenticado)
):
    # Impede livros repetidos no mesmo pedido
    ids = [item.livro_id for item in dados.itens]

    if len(ids) != len(set(ids)):
        raise HTTPException(
            status_code=400,
            detail="Nao repita o mesmo livro no pedido"
        )

    try:
        with conectar_postgres() as conn:
            with conn.cursor() as cur:

                # Verifica se o cliente existe
                cur.execute(
                    "SELECT id FROM clientes WHERE id = %s",
                    (dados.cliente_id,)
                )

                if cur.fetchone() is None:
                    raise HTTPException(
                        status_code=404,
                        detail="Cliente nao encontrado"
                    )

                itens_validados = []
                total = Decimal("0.00")

                # Consulta os precos atuais dos livros
                for item in dados.itens:
                    cur.execute(
                        """
                        SELECT id, preco
                        FROM livros
                        WHERE id = %s
                        """,
                        (item.livro_id,)
                    )

                    livro = cur.fetchone()

                    if livro is None:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Livro {item.livro_id} nao encontrado"
                        )

                    preco = livro[1]
                    subtotal = preco * item.quantidade
                    total += subtotal

                    itens_validados.append({
                        "livro_id": item.livro_id,
                        "quantidade": item.quantidade,
                        "preco_unitario": preco
                    })

                # Cria o pedido
                cur.execute(
                    """
                    INSERT INTO pedidos (cliente_id, status)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (dados.cliente_id, "processando")
                )

                pedido_id = cur.fetchone()[0]

                # Cria os itens associados
                for item in itens_validados:
                    cur.execute(
                        """
                        INSERT INTO itens_pedido
                        (pedido_id, livro_id, quantidade, preco_unitario)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            pedido_id,
                            item["livro_id"],
                            item["quantidade"],
                            item["preco_unitario"]
                        )
                    )

        return {
            "mensagem": "Pedido cadastrado com sucesso",
            "pedido_id": pedido_id,
            "cliente_id": dados.cliente_id,
            "total": float(total),
            "status": "processando"
        }

    except HTTPException:
        raise
    except psycopg.Error:
        raise HTTPException(
            status_code=500,
            detail="Erro ao cadastrar pedido"
        )



# ============================================
# CQRS - SINCRONIZACAO E LEITURA
# ============================================

from fastapi import Query

from app.services.sincronizacao import (
    sincronizar_pedidos,
    consultar_resumos
)


@app.post("/sincronizar")
def sincronizar(
    usuario=Depends(usuario_autenticado)
):
    return sincronizar_pedidos()


@app.get("/relatorios/pedidos")
def relatorio_pedidos(
    limite: int = Query(default=20, ge=1, le=100),
    usuario=Depends(usuario_autenticado)
):
    return consultar_resumos(limite)
