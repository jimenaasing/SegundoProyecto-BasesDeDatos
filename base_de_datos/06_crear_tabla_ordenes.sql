---------------------- Ordenes --------------------

CREATE TABLE orden (
    orden_id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL REFERENCES usuario(usuario_id),
    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE', 'PAGADA', 'CANCELADA')),
    subtotal NUMERIC(10,2) NOT NULL,
    descuento NUMERIC(10,2) NOT NULL DEFAULT 0,
    cargo_servicio NUMERIC(10,2) NOT NULL DEFAULT 0,
    total NUMERIC(10,2) NOT NULL,
    creada_en TIMESTAMP NOT NULL DEFAULT now(),
    CHECK (total = subtotal - descuento + cargo_servicio));

CREATE TABLE bloqueo_asiento (
    bloqueo_id SERIAL PRIMARY KEY,
    orden_id INT NOT NULL REFERENCES orden(orden_id),
    funcion_id INT NOT NULL REFERENCES funcion(funcion_id),
    asiento_id INT NOT NULL REFERENCES asiento(asiento_id),
    expira_en TIMESTAMP NOT NULL,
    UNIQUE (funcion_id, asiento_id));

CREATE TABLE metodo_pago (
    metodo_pago_id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE);

CREATE TABLE pago (
    pago_id SERIAL PRIMARY KEY,
    orden_id INT NOT NULL REFERENCES orden(orden_id),
    metodo_pago_id INT NOT NULL REFERENCES metodo_pago(metodo_pago_id),
    monto NUMERIC(10,2) NOT NULL,
    estado VARCHAR(20) NOT NULL CHECK (estado IN ('APROBADO', 'RECHAZADO')),
    ultimos4 VARCHAR(4),
    creado_en TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE boleto (
    boleto_id SERIAL PRIMARY KEY,
    orden_id INT NOT NULL REFERENCES orden(orden_id),
    funcion_id INT NOT NULL REFERENCES funcion(funcion_id),
    asiento_id INT NOT NULL REFERENCES asiento(asiento_id),
    tipo_entrada_id INT NOT NULL REFERENCES tipo_entrada(tipo_entrada_id),
    precio NUMERIC(10,2) NOT NULL,
    codigo_qr VARCHAR(64) NOT NULL UNIQUE,
    estado VARCHAR(20) NOT NULL DEFAULT 'EMITIDO' CHECK (estado IN ('EMITIDO', 'USADO', 'ANULADO')),
    usado_en TIMESTAMP);

-- Evita que un mismo asiento se venda dos veces en la misma función
CREATE UNIQUE INDEX indice_sin_doble_venta_de_asiento
ON boleto (funcion_id, asiento_id)
WHERE estado <> 'ANULADO';