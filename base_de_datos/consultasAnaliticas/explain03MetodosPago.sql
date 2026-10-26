
-- Consulta 3: Porcentaje de uso de métodos de pago


EXPLAIN (ANALYZE, BUFFERS)

SELECT
    mp.nombre AS metodo_pago,
    COUNT(pa.pago_id) AS pagos_aprobados,
    ROUND(
        COUNT(pa.pago_id) * 100.0 /
        NULLIF(
            (SELECT COUNT(*)
             FROM pago
             WHERE estado = 'APROBADO'), 0
        ), 2
    ) AS porcentaje_uso

FROM metodo_pago mp

LEFT JOIN pago pa
    ON mp.metodo_pago_id = pa.metodo_pago_id
    AND pa.estado = 'APROBADO'

GROUP BY mp.metodo_pago_id, mp.nombre

ORDER BY pagos_aprobados DESC, mp.nombre;
