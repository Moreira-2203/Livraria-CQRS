
-- ===========================================
-- LIVRARIA CQRS - CONSULTAS DE VALIDACAO
-- ===========================================

-- TESTE 1: Quantidade de registros

SELECT 'clientes' AS tabela, COUNT(*) AS total
FROM clientes
UNION ALL
SELECT 'autores', COUNT(*) FROM autores
UNION ALL
SELECT 'categorias', COUNT(*) FROM categorias
UNION ALL
SELECT 'livros', COUNT(*) FROM livros
UNION ALL
SELECT 'pedidos', COUNT(*) FROM pedidos
UNION ALL
SELECT 'itens_pedido', COUNT(*) FROM itens_pedido;


-- TESTE 2: Pedidos com clientes e total

SELECT
    p.id AS pedido_id,
    c.nome AS cliente,
    p.status,
    SUM(i.quantidade * i.preco_unitario) AS total
FROM pedidos p
JOIN clientes c ON c.id = p.cliente_id
JOIN itens_pedido i ON i.pedido_id = p.id
GROUP BY p.id, c.nome, p.status
ORDER BY p.id DESC
LIMIT 10;


-- TESTE 3: Livros e autores

SELECT
    l.titulo,
    a.nome AS autor
FROM livros l
JOIN livros_autores la ON la.livro_id = l.id
JOIN autores a ON a.id = la.autor_id
ORDER BY l.id
LIMIT 20;


-- TESTE 4: Pedidos sem itens

SELECT p.id
FROM pedidos p
LEFT JOIN itens_pedido i ON i.pedido_id = p.id
WHERE i.id IS NULL;


-- TESTE 5: Pedidos com clientes inexistentes

SELECT p.id
FROM pedidos p
LEFT JOIN clientes c ON c.id = p.cliente_id
WHERE c.id IS NULL;


-- TESTE 6: Verificar registros repetidos

SELECT
    pedido_id,
    livro_id,
    COUNT(*) AS quantidade
FROM itens_pedido
GROUP BY pedido_id, livro_id
HAVING COUNT(*) > 1;


-- TESTE 7: Verificar senhas armazenadas
-- Nao exibe os hashes completos

SELECT
    id,
    nome_usuario,
    CASE
        WHEN senha_hash IS NOT NULL
             AND LENGTH(senha_hash) > 30
        THEN 'HASH PRESENTE'
        ELSE 'VERIFICAR'
    END AS seguranca
FROM usuarios;
