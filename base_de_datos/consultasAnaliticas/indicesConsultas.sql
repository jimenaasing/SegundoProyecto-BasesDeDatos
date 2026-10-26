

-- Proyecto 2 IMAX
-- Índices para las consultas analíticas

-- Consulta 1: Ocupación y recaudación
CREATE INDEX IF NOT EXISTS idx_pago_aprobado_orden
ON pago (orden_id)
WHERE estado = 'APROBADO';

-- Consulta 2: Top 5 de películas más vendidas
CREATE INDEX IF NOT EXISTS idx_orden_pagada_fecha
ON orden (creada_en, orden_id)
WHERE estado = 'PAGADA';

-- Consulta 3: Porcentaje de métodos de pago
CREATE INDEX IF NOT EXISTS idx_pago_aprobado_metodo
ON pago (metodo_pago_id)
WHERE estado = 'APROBADO';


-- Consulta 4: Auditoría de operaciones administrativas
CREATE INDEX IF NOT EXISTS idx_auditoria_fecha_accion_usuario
ON public.admin_operacion_audit
(fecha_hora, accion, usuario_id);
