-- Fase 0: banco de dados e tabelas (PostgreSQL)
--
-- Pelo terminal:  psql -U postgres -f 0_criar_banco.sql
-- Pelo pgAdmin:   rode o CREATE DATABASE sozinho, abra uma conexão no banco
--                 novo e rode o restante (sem a linha \connect).

CREATE DATABASE viagens_transparencia;

\connect viagens_transparencia

-- Recria tudo do zero (filhas primeiro, por causa das chaves estrangeiras)
DROP TABLE IF EXISTS silver_trecho;
DROP TABLE IF EXISTS silver_pagamento;
DROP TABLE IF EXISTS silver_passagem;
DROP TABLE IF EXISTS silver_viagem;
DROP TABLE IF EXISTS raw_trecho;
DROP TABLE IF EXISTS raw_pagamento;
DROP TABLE IF EXISTS raw_passagem;
DROP TABLE IF EXISTS raw_viagem;


-- ============================================================
-- CAMADA RAW: cópia fiel dos CSVs. Tudo VARCHAR, sem constraints.
-- ============================================================

CREATE TABLE raw_viagem (
    id_processo_viagem      VARCHAR,
    num_proposta            VARCHAR,
    situacao                VARCHAR,
    viagem_urgente          VARCHAR,
    justificativa_urgencia  VARCHAR,
    cod_orgao_superior      VARCHAR,
    nome_orgao_superior     VARCHAR,
    cod_orgao_solicitante   VARCHAR,
    nome_orgao_solicitante  VARCHAR,
    cpf_viajante            VARCHAR,
    nome                    VARCHAR,
    cargo                   VARCHAR,
    funcao                  VARCHAR,
    descricao_funcao        VARCHAR,
    data_inicio             VARCHAR,
    data_fim                VARCHAR,
    destinos                VARCHAR,
    motivo                  VARCHAR,
    valor_diarias           VARCHAR,
    valor_passagens         VARCHAR,
    valor_devolucao         VARCHAR,
    valor_outros_gastos     VARCHAR
);

CREATE TABLE raw_pagamento (
    id_processo_viagem   VARCHAR,
    num_proposta         VARCHAR,
    cod_orgao_superior   VARCHAR,
    nome_orgao_superior  VARCHAR,
    cod_orgao_pagador    VARCHAR,
    nome_orgao_pagador   VARCHAR,
    cod_ug_pagadora      VARCHAR,
    nome_ug_pagadora     VARCHAR,
    tipo_pagamento       VARCHAR,
    valor                VARCHAR
);

CREATE TABLE raw_passagem (
    id_processo_viagem   VARCHAR,
    num_proposta         VARCHAR,
    meio_transporte      VARCHAR,
    pais_origem_ida      VARCHAR,
    uf_origem_ida        VARCHAR,
    cidade_origem_ida    VARCHAR,
    pais_destino_ida     VARCHAR,
    uf_destino_ida       VARCHAR,
    cidade_destino_ida   VARCHAR,
    pais_origem_volta    VARCHAR,
    uf_origem_volta      VARCHAR,
    cidade_origem_volta  VARCHAR,
    pais_destino_volta   VARCHAR,
    uf_destino_volta     VARCHAR,
    cidade_destino_volta VARCHAR,
    valor_passagem       VARCHAR,
    taxa_servico         VARCHAR,
    data_emissao         VARCHAR,
    hora_emissao         VARCHAR
);

CREATE TABLE raw_trecho (
    id_processo_viagem  VARCHAR,
    num_proposta        VARCHAR,
    sequencia_trecho    VARCHAR,
    origem_data         VARCHAR,
    origem_pais         VARCHAR,
    origem_uf           VARCHAR,
    origem_cidade       VARCHAR,
    destino_data        VARCHAR,
    destino_pais        VARCHAR,
    destino_uf          VARCHAR,
    destino_cidade      VARCHAR,
    meio_transporte     VARCHAR,
    numero_diarias      VARCHAR,
    missao              VARCHAR
);
