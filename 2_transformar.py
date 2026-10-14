"""Fase 2: transformação Raw -> Silver.

Lê as tabelas raw_* em blocos, converte os tipos (texto -> DECIMAL e DATE),
calcula valor_total e duracao_dias e grava nas tabelas silver_*, respeitando
as chaves estrangeiras (a viagem é carregada primeiro).

Linhas que quebrariam alguma regra (id vazio, id repetido, valor negativo,
viagem inexistente...) não entram na Silver e são contadas no resumo final.
O processo todo roda em uma transação: se der erro, nada é alterado.
"""
import sys
import time
from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation

import banco
import config

CENTAVOS = Decimal("0.01")



# Funções de conversão

def limpar_texto(texto):
    """Tira espaços das pontas; texto vazio vira None."""
    if texto is None:
        return None
    texto = texto.strip()
    return texto or None


def converter_decimal(texto):
    """'1272,97' (ou '1.272,97') -> Decimal('1272.97'). Inválido -> None."""
    texto = limpar_texto(texto)
    if texto is None:
        return None
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return Decimal(texto).quantize(CENTAVOS)
    except InvalidOperation:
        return None


def converter_data(texto):
    """'25/01/2025' -> date(2025, 1, 25). Inválido ou vazio -> None."""
    texto = limpar_texto(texto)
    if texto is None:
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date()
    except ValueError:
        return None


def converter_inteiro(texto):
    texto = limpar_texto(texto)
    if texto is None:
        return None
    try:
        return int(texto)
    except ValueError:
        return None


def calcular_valor_total(diarias, passagens, outros, devolucao):
    """Diárias + passagens + outros gastos - devolução."""
    partes = [v or Decimal("0") for v in (diarias, passagens, outros)]
    return sum(partes) - (devolucao or Decimal("0"))


def calcular_duracao(inicio, fim):
    if inicio is None or fim is None:
        return None
    dias = (fim - inicio).days
    return dias + 1 if config.DURACAO_INCLUSIVA else dias


def negativo(*valores):
    return any(v is not None and v < 0 for v in valores)



# Regras de cada tabela: recebem a linha Raw e devolvem
# (tupla para a Silver, None) ou (None, motivo_da_rejeicao)

def regra_viagem(linha, ctx):
    (id_viagem, proposta, situacao, urgente, cod_orgao, orgao, nome, cargo,
    inicio, fim, destinos, motivo, diarias, passagens, devolucao,
    outros) = linha

    id_viagem = limpar_texto(id_viagem)
    orgao = limpar_texto(orgao)
    if id_viagem is None:
        return None, "id_viagem vazio"
    if id_viagem in ctx["ids"]:
        return None, "id_viagem repetido"
    if orgao is None:
        return None, "nome_orgao_superior vazio"

    diarias = converter_decimal(diarias)
    passagens = converter_decimal(passagens)
    devolucao = converter_decimal(devolucao)
    outros = converter_decimal(outros)
    if negativo(diarias):
        return None, "valor_diarias negativo"

    inicio = converter_data(inicio)
    fim = converter_data(fim)
    ctx["ids"].add(id_viagem)
    return (
        id_viagem, limpar_texto(proposta), limpar_texto(situacao),
        limpar_texto(urgente), limpar_texto(cod_orgao), orgao,
        limpar_texto(nome), limpar_texto(cargo), inicio, fim,
        limpar_texto(destinos), limpar_texto(motivo), diarias, passagens,
        devolucao, outros,
        calcular_valor_total(diarias, passagens, outros, devolucao),
        calcular_duracao(inicio, fim),
    ), None


def regra_pagamento(linha, ctx):
    id_viagem, proposta, orgao_pagador, ug_pagadora, tipo, valor = linha
    id_viagem = limpar_texto(id_viagem)
    if id_viagem not in ctx["ids"]:
        return None, "viagem inexistente"
    tipo = limpar_texto(tipo)
    if tipo is None:
        return None, "tipo_pagamento vazio"
    valor = converter_decimal(valor)
    if negativo(valor):
        return None, "valor negativo"
    return (id_viagem, limpar_texto(proposta), limpar_texto(orgao_pagador),
            limpar_texto(ug_pagadora), tipo, valor), None


def regra_passagem(linha, ctx):
    (id_viagem, meio, pais_o, uf_o, cidade_o, pais_d, uf_d, cidade_d,
    valor, taxa, emissao) = linha
    id_viagem = limpar_texto(id_viagem)
    if id_viagem not in ctx["ids"]:
        return None, "viagem inexistente"
    valor = converter_decimal(valor)
    taxa = converter_decimal(taxa)
    if negativo(valor, taxa):
        return None, "valor ou taxa negativo"
    return (id_viagem, limpar_texto(meio), limpar_texto(pais_o),
            limpar_texto(uf_o), limpar_texto(cidade_o), limpar_texto(pais_d),
            limpar_texto(uf_d), limpar_texto(cidade_d), valor, taxa,
            converter_data(emissao)), None


def regra_trecho(linha, ctx):
    (id_viagem, sequencia, data_o, uf_o, cidade_o, data_d, uf_d, cidade_d,
    meio, diarias) = linha
    id_viagem = limpar_texto(id_viagem)
    if id_viagem not in ctx["ids"]:
        return None, "viagem inexistente"
    sequencia = converter_inteiro(sequencia)
    if sequencia is not None:
        chave = (id_viagem, sequencia)
        if chave in ctx["trechos"]:
            return None, "trecho repetido (id_viagem, sequencia)"
        ctx["trechos"].add(chave)
    diarias = converter_decimal(diarias)
    if negativo(diarias):
        return None, "numero_diarias negativo"
    return (id_viagem, sequencia, converter_data(data_o), limpar_texto(uf_o),
            limpar_texto(cidade_o), converter_data(data_d),
            limpar_texto(uf_d), limpar_texto(cidade_d), limpar_texto(meio),
            diarias), None


# A viagem precisa existir antes das tabelas que a referenciam.
ETAPAS = [
    {
        "origem": "raw_viagem", "destino": "silver_viagem",
        "colunas_raw": ["id_processo_viagem", "num_proposta", "situacao",
                        "viagem_urgente", "cod_orgao_superior",
                        "nome_orgao_superior", "nome", "cargo", "data_inicio",
                        "data_fim", "destinos", "motivo", "valor_diarias",
                        "valor_passagens", "valor_devolucao",
                        "valor_outros_gastos"],
        "colunas_silver": ["id_viagem", "num_proposta", "situacao",
                        "viagem_urgente", "cod_orgao_superior",
                        "nome_orgao_superior", "nome_viajante", "cargo",
                        "data_inicio", "data_fim", "destinos", "motivo",
                        "valor_diarias", "valor_passagens",
                        "valor_devolucao", "valor_outros_gastos",
                        "valor_total", "duracao_dias"],
        "regra": regra_viagem,
    },
    {
        "origem": "raw_pagamento", "destino": "silver_pagamento",
        "colunas_raw": ["id_processo_viagem", "num_proposta",
                        "nome_orgao_pagador", "nome_ug_pagadora",
                        "tipo_pagamento", "valor"],
        "colunas_silver": ["id_viagem", "num_proposta", "nome_orgao_pagador",
                        "nome_ug_pagadora", "tipo_pagamento", "valor"],
        "regra": regra_pagamento,
    },
    {
        "origem": "raw_passagem", "destino": "silver_passagem",
        "colunas_raw": ["id_processo_viagem", "meio_transporte",
                        "pais_origem_ida", "uf_origem_ida",
                        "cidade_origem_ida", "pais_destino_ida",
                        "uf_destino_ida", "cidade_destino_ida",
                        "valor_passagem", "taxa_servico", "data_emissao"],
        "colunas_silver": ["id_viagem", "meio_transporte", "pais_origem_ida",
                        "uf_origem_ida", "cidade_origem_ida",
                        "pais_destino_ida", "uf_destino_ida",
                        "cidade_destino_ida", "valor_passagem",
                        "taxa_servico", "data_emissao"],
        "regra": regra_passagem,
    },
    {
        "origem": "raw_trecho", "destino": "silver_trecho",
        "colunas_raw": ["id_processo_viagem", "sequencia_trecho",
                        "origem_data", "origem_uf", "origem_cidade",
                        "destino_data", "destino_uf", "destino_cidade",
                        "meio_transporte", "numero_diarias"],
        "colunas_silver": ["id_viagem", "sequencia_trecho", "origem_data",
                        "origem_uf", "origem_cidade", "destino_data",
                        "destino_uf", "destino_cidade", "meio_transporte",
                        "numero_diarias"],
        "regra": regra_trecho,
    },
]


def transformar_etapa(conn, etapa, ctx):
    """Lê a tabela Raw em blocos, aplica a regra e grava na Silver."""
    rejeitados = Counter()
    lidas = gravadas = 0

    sql = f"SELECT {', '.join(etapa['colunas_raw'])} FROM {etapa['origem']}"
    with conn.cursor(name=f"cur_{etapa['origem']}") as cur:
        cur.itersize = config.TAMANHO_BLOCO
        cur.execute(sql)
        while True:
            bloco = cur.fetchmany(config.TAMANHO_BLOCO)
            if not bloco:
                break
            validas = []
            for linha in bloco:
                nova, motivo = etapa["regra"](linha, ctx)
                if nova is None:
                    rejeitados[motivo] += 1
                else:
                    validas.append(nova)
            lidas += len(bloco)
            gravadas += len(validas)
            banco.inserir_em_lote(conn, etapa["destino"],
                                etapa["colunas_silver"], validas)
    return lidas, gravadas, rejeitados


def main():
    conn = banco.conectar()
    ctx = {"ids": set(), "trechos": set()}
    try:
        # filhas e pai juntos, para o Postgres aceitar o TRUNCATE com FK
        banco.executar(conn, "TRUNCATE TABLE silver_trecho, silver_pagamento, "
                            "silver_passagem, silver_viagem "
                            "RESTART IDENTITY")
        for etapa in ETAPAS:
            inicio = time.time()
            lidas, gravadas, rejeitados = transformar_etapa(conn, etapa, ctx)
            print(f"{etapa['destino']}: {lidas:,} lidas, {gravadas:,} "
                f"gravadas ({time.time() - inicio:.0f}s)")
            for motivo, qtd in rejeitados.items():
                print(f"    rejeitadas ({motivo}): {qtd:,}")
        conn.commit()
        print("Camada Silver carregada.")
    except Exception as erro:
        conn.rollback()
        print(f"Erro na transformação, nada foi alterado: {erro}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
