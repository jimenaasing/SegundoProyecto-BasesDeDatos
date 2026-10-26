
-- Consulta 2: Top 5 de películas más vendidas
-- durante la última semana



SELECT
    p.titulo AS pelicula,
    COUNT(b.boleto_id) AS boletos_vendidos

FROM pelicula p

INNER JOIN funcion f
    ON p.pelicula_id = f.pelicula_id

INNER JOIN boleto b
    ON f.funcion_id = b.funcion_id

INNER JOIN orden o
    ON b.orden_id = o.orden_id

WHERE o.estado = 'PAGADA'
    AND b.estado IN ('EMITIDO', 'USADO')
    AND o.creada_en >= NOW() - INTERVAL '7 days'
    AND o.creada_en <= NOW()
    AND EXISTS (
        SELECT 1
        FROM pago pa
        WHERE pa.orden_id = o.orden_id
          AND pa.estado = 'APROBADO'
    )

GROUP BY p.pelicula_id, p.titulo

ORDER BY boletos_vendidos DESC, p.titulo

LIMIT 5;
