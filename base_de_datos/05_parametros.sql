--------------------- Parametros --------------------

CREATE TABLE parametro_sistema (
    clave VARCHAR(50) PRIMARY KEY,
    valor VARCHAR(100) NOT NULL);

INSERT INTO parametro_sistema (clave,valor) VALUES
    ('MAX_ASIENTOS_ORDEN', '6'),
    ('MINUTOS_BLOQUEO','2'),
    ('MINUTOS_ANTES_INGRESO', '30'),
    ('MINUTOS_DESPUES_INGRESO','15'),
    ('HORAS_LIMITE_REEMBOLSO','2');