"""Configurações do projeto.

Lê as credenciais do arquivo .env (que fica fora do Git) e reúne
os parâmetros usados pelos scripts do pipeline.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- Banco de dados (PostgreSQL) ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "viagens_transparencia")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# --- Origem dos dados ---
# Cole aqui o ID do arquivo no Google Drive (ou defina DRIVE_FILE_ID no .env).
DRIVE_FILE_ID = os.getenv("DRIVE_FILE_ID") or "COLE_O_ID_AQUI"
DATA_DIR = BASE_DIR / "data"
ZIP_PATH = DATA_DIR / "viagens_2025.zip"

# --- Leitura dos CSVs ---
CSV_SEPARADOR = ";"
CSV_ENCODING = "latin-1"
TAMANHO_BLOCO = 20_000  # linhas lidas por vez do CSV / do banco
TAMANHO_LOTE = 5_000    # linhas por INSERT

# A duração conta o dia de início e o de fim (25/01 a 01/02 = 8 dias).
# Mude para False para usar apenas a diferença entre as datas (7 dias).
DURACAO_INCLUSIVA = True

# Tabela Raw -> (arquivo CSV, colunas na ordem em que aparecem no arquivo).
# O cabeçalho original dos CSVs é substituído por estes nomes (snake_case).
ARQUIVOS_RAW = {
    "raw_viagem": (
        "2025_Viagem.csv",
        [
            "id_processo_viagem", "num_proposta", "situacao", "viagem_urgente",
            "justificativa_urgencia", "cod_orgao_superior",
            "nome_orgao_superior", "cod_orgao_solicitante",
            "nome_orgao_solicitante", "cpf_viajante", "nome", "cargo",
            "funcao", "descricao_funcao", "data_inicio", "data_fim",
            "destinos", "motivo", "valor_diarias", "valor_passagens",
            "valor_devolucao", "valor_outros_gastos",
        ],
    ),
    "raw_pagamento": (
        "2025_Pagamento.csv",
        [
            "id_processo_viagem", "num_proposta", "cod_orgao_superior",
            "nome_orgao_superior", "cod_orgao_pagador", "nome_orgao_pagador",
            "cod_ug_pagadora", "nome_ug_pagadora", "tipo_pagamento", "valor",
        ],
    ),
    "raw_passagem": (
        "2025_Passagem.csv",
        [
            "id_processo_viagem", "num_proposta", "meio_transporte",
            "pais_origem_ida", "uf_origem_ida", "cidade_origem_ida",
            "pais_destino_ida", "uf_destino_ida", "cidade_destino_ida",
            "pais_origem_volta", "uf_origem_volta", "cidade_origem_volta",
            "pais_destino_volta", "uf_destino_volta", "cidade_destino_volta",
            "valor_passagem", "taxa_servico", "data_emissao", "hora_emissao",
        ],
    ),
    "raw_trecho": (
        "2025_Trecho.csv",
        [
            "id_processo_viagem", "num_proposta", "sequencia_trecho",
            "origem_data", "origem_pais", "origem_uf", "origem_cidade",
            "destino_data", "destino_pais", "destino_uf", "destino_cidade",
            "meio_transporte", "numero_diarias", "missao",
        ],
    ),
}
