
-- Proyecto II IMAX
-- Datos de prueba para auditoría administrativa

INSERT INTO public.admin_operacion_audit
(usuario_id, fecha_hora, accion, detalle, direccion_ip)
VALUES
(6, NOW() - INTERVAL '1 day',
 'MODIFICAR_TARIFA',
 'PRUEBA: Se modificó el precio de una entrada.',
 '127.0.0.1'),

(6, NOW() - INTERVAL '3 days',
 'ACTUALIZAR_PELICULA',
 'PRUEBA: Se actualizó la información de una película.',
 '127.0.0.1'),

(6, NOW() - INTERVAL '6 days',
 'DESACTIVAR_PROMOCION',
 'PRUEBA: Se desactivó una promoción.',
 '127.0.0.1'),

(6, NOW() - INTERVAL '12 days',
 'MODIFICAR_FUNCION',
 'PRUEBA: Se modificó el horario de una función.',
 '127.0.0.1'),

(6, NOW() - INTERVAL '20 days',
 'ACTUALIZAR_USUARIO',
 'PRUEBA: Se modificó la información de un usuario.',
 '127.0.0.1'),

(6, NOW() - INTERVAL '28 days',
 'ACTIVAR_PROMOCION',
 'PRUEBA: Se activó una promoción.',
 '127.0.0.1'),

(6, NOW() - INTERVAL '40 days',
 'MODIFICAR_TARIFA',
 'PRUEBA: Se modificó una tarifa antigua.',
 '127.0.0.1'),

(6, NOW() - INTERVAL '2 days',
 'OTORGAR_CORTESIA',
 'PRUEBA: El administrador otorgó una entrada de cortesía.',
 '127.0.0.1'),

(6, NOW() - INTERVAL '4 days',
 'REEMBOLSO_FORZADO',
 'PRUEBA: El administrador autorizó un reembolso manual.',
 '127.0.0.1');

-- Verificar cantidad de registros
SELECT COUNT(*) AS total_registros
FROM public.admin_operacion_audit;
