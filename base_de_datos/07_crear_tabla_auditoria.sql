
-- Proyecto II IMAX
-- Tabla de auditoría de operaciones administrativas

CREATE TABLE public.admin_operacion_audit (
    auditoria_id BIGINT GENERATED ALWAYS AS IDENTITY,
    usuario_id INT NOT NULL REFERENCES public.usuario(usuario_id),
    fecha_hora TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    accion VARCHAR(50) NOT NULL,
    detalle TEXT NOT NULL,
    direccion_ip INET,

    PRIMARY KEY (auditoria_id, fecha_hora)
) PARTITION BY RANGE (fecha_hora);

-- Registros de septiembre de 2026
CREATE TABLE public.admin_operacion_audit_2026_09
PARTITION OF public.admin_operacion_audit
FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');

-- Registros de octubre de 2026
CREATE TABLE public.admin_operacion_audit_2026_10
PARTITION OF public.admin_operacion_audit
FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

-- Registros de noviembre de 2026
CREATE TABLE public.admin_operacion_audit_2026_11
PARTITION OF public.admin_operacion_audit
FOR VALUES FROM ('2026-11-01') TO ('2026-12-01');

-- Recibe fechas de otros meses
CREATE TABLE public.admin_operacion_audit_otros
PARTITION OF public.admin_operacion_audit DEFAULT;
