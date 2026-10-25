---------------------- Peliculas --------------------
-- guarda primero pelicula, luego crea genero y ya puede ponerle el genero a la pelicula, luego se guardan las funciones de cada pelicula
CREATE TABLE pelicula (
    pelicula_id SERIAL PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    sinopsis TEXT NOT NULL,
    clasificacion VARCHAR(10) NOT NULL,
    duracion_min INT NOT NULL CHECK (duracion_min > 0),
    poster_url VARCHAR(300),
    activa BOOLEAN NOT NULL DEFAULT TRUE);

CREATE TABLE genero (
    genero_id SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE);


CREATE TABLE pelicula_genero (
    pelicula_id INT NOT NULL REFERENCES pelicula(pelicula_id),
    genero_id INT NOT NULL REFERENCES genero(genero_id),
    PRIMARY KEY (pelicula_id, genero_id)
);

CREATE TABLE funcion (
    funcion_id SERIAL PRIMARY KEY,
    pelicula_id INT NOT NULL REFERENCES pelicula(pelicula_id),
    sala_id INT NOT NULL REFERENCES sala(sala_id),
    inicio TIMESTAMP NOT NULL,
    fin TIMESTAMP NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    CHECK (fin > inicio)
);