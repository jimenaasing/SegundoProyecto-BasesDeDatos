-- Proyecto 2 IMAX - Crear tablas para el cine
---------------------- Cines ----------------------
-- crea la tabla de todos los cines con su ubicacion
CREATE TABLE cine (
    cine_id SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    ciudad VARCHAR(100) NOT NULL,
    direccion VARCHAR(200) NOT NULL
);

---------------------- Salas ----------------------
-- crea la tabla de las zonas dentro de la sala de cine
CREATE TABLE zona (
    zona_id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE);

-- crea la tabla que guarda las salas, en que cines estan, como se llaman y cuanta gente cabe
CREATE TABLE sala (
    sala_id SERIAL PRIMARY KEY,
    cine_id INT NOT NULL REFERENCES cine(cine_id),
    nombre VARCHAR(50) NOT NULL,
    capacidad INT NOT NULL CHECK (capacidad > 0),
    -- no se repite nombre de la sala dentro del mismo cine
    UNIQUE (cine_id, nombre));

-- crea la tabla que almacena los datos de los asientos, en que sala estan, a que zona pertenece y cual es si fila y numero
CREATE TABLE asiento (
    asiento_id SERIAL PRIMARY KEY,
    sala_id INT NOT NULL REFERENCES sala(sala_id),
    zona_id INT NOT NULL REFERENCES zona(zona_id),
    fila VARCHAR(2) NOT NULL,
    numero INT NOT NULL CHECK (numero > 0),
    -- dentro de una sala no puede repetirse el mismo numero de asiento
    UNIQUE (sala_id, fila, numero));