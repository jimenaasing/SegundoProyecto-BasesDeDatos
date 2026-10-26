
-- Consulta 4: Auditoría de operaciones administrativas
-- Operaciones realizadas durante el último mes


SELECT
    a.usuario_id AS administrador_id,
    u.nombre AS administrador,
    COUNT(*) FILTER (
        WHERE a.accion IN (
            'MODIFICAR_TARIFA',
            'ACTUALIZAR_PELICULA',
            'DESACTIVAR_PROMOCION',
            'MODIFICAR_FUNCION',
            'ACTUALIZAR_USUARIO',
            'ACTIVAR_PROMOCION'
        )
    ) AS modificaciones_manuales,
    COUNT(*) FILTER (
        WHERE a.accion = 'OTORGAR_CORTESIA'
    ) AS cortesias_otorgadas,
    COUNT(*) FILTER (
        WHERE a.accion = 'REEMBOLSO_FORZADO'
    ) AS reembolsos,
    COUNT(*) AS total_operaciones
FROM public.admin_operacion_audit a
INNER JOIN public.usuario u
    ON a.usuario_id = u.usuario_id
INNER JOIN public.rol r
    ON u.rol_id = r.rol_id
WHERE r.nombre = 'ADMIN'
    AND a.fecha_hora >= NOW() - INTERVAL '1 month'
    AND a.fecha_hora <= NOW()
    AND a.accion IN (
        'MODIFICAR_TARIFA',
        'ACTUALIZAR_PELICULA',
        'DESACTIVAR_PROMOCION',
        'MODIFICAR_FUNCION',
        'ACTUALIZAR_USUARIO',
        'ACTIVAR_PROMOCION',
        'OTORGAR_CORTESIA',
        'REEMBOLSO_FORZADO'
    )
GROUP BY a.usuario_id, u.nombre
ORDER BY total_operaciones DESC;
