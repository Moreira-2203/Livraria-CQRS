
-- =========================================================
-- LIVRARIA CQRS - HISTORICO DE MIGRACAO
-- Da estrutura inicial para a estrutura definitiva
-- =========================================================

-- Execute apenas em um banco que possua
-- o esquema INICIAL da atividade.
-- Nao execute sobre o esquema definitivo novo.

ALTER TABLE clientes
    ADD COLUMN IF NOT EXISTS cidade VARCHAR(150),
    ADD COLUMN IF NOT EXISTS estado VARCHAR(2),
    ADD COLUMN IF NOT EXISTS membro_desde DATE;

ALTER TABLE autores
    ADD COLUMN IF NOT EXISTS nacionalidade VARCHAR(100),
    ADD COLUMN IF NOT EXISTS ano_nascimento INTEGER;

ALTER TABLE categorias
    ADD COLUMN IF NOT EXISTS descricao TEXT;

ALTER TABLE livros
    ADD COLUMN IF NOT EXISTS ano_publicacao INTEGER,
    ADD COLUMN IF NOT EXISTS avaliacao_media NUMERIC(3,2);

-- Remove a restricao inicial de status,
-- permitindo preservar os valores do Neo4j
ALTER TABLE pedidos
    DROP CONSTRAINT IF EXISTS pedidos_status_check;

-- O banco inicial ja possui as tabelas e
-- restricoes de integridade referencial.
