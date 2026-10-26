
-- Consulta 1: Ocupación y recaudación por función



WITH ventas AS (
    SELECT
        b.funcion_id,
        o.orden_id,
        COUNT(*) AS boletos_vendidos,
        o.total
    FROM boleto b
    INNER JOIN orden o
        ON b.orden_id = o.orden_id
    WHERE o.estado = 'PAGADA'
      AND b.estado IN ('EMITIDO', 'USADO')
      AND EXISTS (
          SELECT 1
          FROM pago pa
          WHERE pa.orden_id = o.orden_id
            AND pa.estado = 'APROBADO'
      )
    GROUP BY b.funcion_id, o.orden_id, o.total
)

SELECT
    f.funcion_id,
    p.titulo AS pelicula,
    s.nombre AS sala,
    s.capacidad,
    COALESCE(SUM(v.boletos_vendidos), 0)
        AS asientos_vendidos,
    ROUND(
        COALESCE(SUM(v.boletos_vendidos), 0)
        * 100.0 / s.capacidad, 2
    ) AS porcentaje_ocupacion,
    COALESCE(SUM(v.total), 0)
        AS recaudacion_total

FROM funcion f
INNER JOIN pelicula p
    ON f.pelicula_id = p.pelicula_id
INNER JOIN sala s
    ON f.sala_id = s.sala_id
LEFT JOIN ventas v
    ON f.funcion_id = v.funcion_id

GROUP BY
    f.funcion_id,
    p.titulo,
    s.nombre,
    s.capacidad

ORDER BY f.funcion_id;
