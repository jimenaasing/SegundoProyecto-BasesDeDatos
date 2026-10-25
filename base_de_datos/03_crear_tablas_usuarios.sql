---------------------- Usuarios --------------------
-- crea el rol primero, luego se crea usuario para poder asignarle rol
CREATE TABLE rol (
    rol_id SERIAL PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL UNIQUE);

CREATE TABLE usuario (
    usuario_id SERIAL PRIMARY KEY,
    rol_id INT NOT NULL REFERENCES rol(rol_id),
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE);

