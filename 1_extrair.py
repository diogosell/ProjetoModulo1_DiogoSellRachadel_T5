"""Fase 1: extração e carga da camada Raw.

Baixa o .zip do Google Drive, lê os 4 CSVs em blocos e grava nas tabelas
raw_* exatamente como vieram (tudo texto). Pode rodar quantas vezes quiser:
cada tabela é esvaziada (TRUNCATE) antes da carga, então não duplica linhas.

Uso:
    python 1_extrair.py                   # baixa só se faltar algum CSV
    python 1_extrair.py --forcar-download # baixa o zip de novo
"""
import argparse
import sys
import time
import zipfile

import gdown
import pandas as pd

import banco
import config


def csvs_presentes():
    return all((config.DATA_DIR / arq).exists()
               for arq, _ in config.ARQUIVOS_RAW.values())


def baixar_zip():
    """Baixa o .zip do Google Drive para a pasta data/."""
    if config.DRIVE_FILE_ID == "COLE_O_ID_AQUI":
        raise ValueError("Defina o DRIVE_FILE_ID no config.py ou no .env")
    config.DATA_DIR.mkdir(exist_ok=True)
    print("Baixando o arquivo do Google Drive...")
    caminho = gdown.download(id=config.DRIVE_FILE_ID,
                             output=str(config.ZIP_PATH), quiet=False)
    if caminho is None:
        raise RuntimeError("Não foi possível baixar o arquivo do Drive")


def extrair_csvs():
    """Extrai do zip só os 4 CSVs esperados, ignorando subpastas."""
    esperados = {arq for arq, _ in config.ARQUIVOS_RAW.values()}
    with zipfile.ZipFile(config.ZIP_PATH) as zf:
        for nome in zf.namelist():
            base = nome.replace("\\", "/").split("/")[-1]
            if base in esperados:
                destino = config.DATA_DIR / base
                destino.write_bytes(zf.read(nome))
                print(f"  extraído: {base}")


def carregar_tabela(conn, tabela, arquivo, colunas):
    """Esvazia a tabela Raw e carrega o CSV em blocos, sem alterar nada."""
    caminho = config.DATA_DIR / arquivo
    banco.executar(conn, f"TRUNCATE TABLE {tabela}")

    blocos = pd.read_csv(
        caminho,
        sep=config.CSV_SEPARADOR,
        encoding=config.CSV_ENCODING,
        dtype=str,               # tudo texto, como no arquivo
        keep_default_na=False,   # vazio continua vazio (não vira NaN)
        header=0,
        names=colunas,           # troca o cabeçalho original pelos nomes Raw
        chunksize=config.TAMANHO_BLOCO,
    )
    total = 0
    for bloco in blocos:
        banco.inserir_em_lote(conn, tabela, colunas,
                              bloco.itertuples(index=False, name=None))
        total += len(bloco)
    return total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--forcar-download", action="store_true")
    args = parser.parse_args()

    try:
        if args.forcar_download or not csvs_presentes():
            baixar_zip()
            extrair_csvs()
        else:
            print("CSVs já estão em data/, pulando o download.")
    except Exception as erro:
        print(f"Erro na obtenção dos arquivos: {erro}")
        sys.exit(1)

    conn = banco.conectar()
    falhas = 0
    for tabela, (arquivo, colunas) in config.ARQUIVOS_RAW.items():
        inicio = time.time()
        try:
            total = carregar_tabela(conn, tabela, arquivo, colunas)
            conn.commit()  # TRUNCATE + carga valem juntos, ou nada vale
            no_banco = banco.contar_linhas(conn, tabela)
            print(f"{tabela}: {total:,} linhas lidas, {no_banco:,} no banco "
                  f"({time.time() - inicio:.0f}s)")
        except Exception as erro:
            conn.rollback()
            falhas += 1
            print(f"Erro ao carregar {tabela}: {erro}")
    conn.close()
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
