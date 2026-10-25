--------------------- Info de entradas --------------------

-- este era el que dice si es adulto, niño, estudiante o viejito
CREATE TABLE tipo_entrada (
    tipo_entrada_id SERIAL PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE
);
-- la tarifa guarda la informacion de la zona, tipo de entrada y dia de la semana porque en base a eso se calcula  
CREATE TABLE tarifa (
    tarifa_id SERIAL PRIMARY KEY,
    zona_id INT NOT NULL REFERENCES zona(zona_id),
    tipo_entrada_id INT NOT NULL REFERENCES tipo_entrada(tipo_entrada_id),
    dia_semana INT NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    precio NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
    UNIQUE (zona_id, tipo_entrada_id, dia_semana)
);

CREATE TABLE promocion (
    promocion_id SERIAL PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('2X1')),
    dia_semana INT CHECK (dia_semana BETWEEN 0 AND 6),
    activa BOOLEAN NOT NULL DEFAULT TRUE
);
