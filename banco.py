"""Conexão com o PostgreSQL e funções utilitárias."""
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

import config


def conectar():
    """Abre uma conexão psycopg2 com os dados do .env."""
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )


def criar_engine():
    """Engine do SQLAlchemy (usada no notebook com pandas.read_sql)."""
    url = URL.create(
        "postgresql+psycopg2",
        username=config.DB_USER,
        password=config.DB_PASSWORD,
        host=config.DB_HOST,
        port=int(config.DB_PORT),
        database=config.DB_NAME,
    )
    return create_engine(url)


def executar(conn, sql, parametros=None):
    """Executa um comando SQL. O commit fica por conta de quem chama."""
    with conn.cursor() as cur:
        cur.execute(sql, parametros)


def contar_linhas(conn, tabela):
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {tabela}")
        return cur.fetchone()[0]


def inserir_em_lote(conn, tabela, colunas, linhas,
                    tamanho_lote=config.TAMANHO_LOTE):
    """Insere várias linhas de uma vez (muito mais rápido que uma a uma)."""
    sql = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES %s"
    with conn.cursor() as cur:
        execute_values(cur, sql, list(linhas), page_size=tamanho_lote)
