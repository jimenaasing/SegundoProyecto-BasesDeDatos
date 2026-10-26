-------------------- Usarios --------------------
-- Cambio: ahora en lugar de solo nombre ahora queda el id del rol fijo para evitar que se siga incrementando
INSERT INTO rol (rol_id, nombre) VALUES (1, 'CLIENTE');
INSERT INTO rol (rol_id, nombre) VALUES (2, 'TAQUILLERO');
INSERT INTO rol (rol_id, nombre) VALUES (3, 'OPERADOR_PUERTA');
INSERT INTO rol (rol_id, nombre) VALUES (4, 'CONTADOR');
INSERT INTO rol (rol_id, nombre) VALUES (5, 'ADMIN');
-- Cambio: Alinea el contador de ids con el ultimo id escrito a mano
SELECT setval('rol_rol_id_seq', 5);

INSERT INTO usuario (rol_id, nombre, email, password_hash) VALUES (1, 'Anton Ego', 'ego.critic@michelin.fr', 'hash_de_prueba');
INSERT INTO usuario (rol_id, nombre, email, password_hash) VALUES (1, 'Sonia Mora', 'smora@tec.cr', 'hash_de_prueba');
INSERT INTO usuario (rol_id, nombre, email, password_hash) VALUES (2, 'Andre Bourgois', 'bourgois.productions@imax.cr', 'hash_de_prueba');
INSERT INTO usuario (rol_id, nombre, email, password_hash) VALUES (3, 'Teobaldo Jacindo del Sagreado Corazon de Jesus', 'tjdjesus@imax.cr', 'hash_de_prueba');
INSERT INTO usuario (rol_id, nombre, email, password_hash) VALUES (4, 'Chayanne', 'chayanne.@imax.cr', 'hash_de_prueba');
INSERT INTO usuario (rol_id, nombre, email, password_hash) VALUES (5, 'Vassago Goetia', 'vassagocarmesi@imax.cr', 'hash_de_prueba');

-- -------------------- Cines --------------------

INSERT INTO cine (nombre, ciudad, direccion) VALUES ('IMAX Chepe Centro', 'San Jose', 'A 300 metros de la soda ta bueno');
INSERT INTO cine (nombre, ciudad, direccion) VALUES ('IMAX Paseo Metropoli', 'Cartago', 'A 1km del cementerio, como yendo para san jose');
-- Cambio: ahora en lugar de solo nombre ahora queda el id del rol fijo para evitar que se siga incrementando
INSERT INTO zona (zona_id, nombre) VALUES (1, 'PLATEA');
INSERT INTO zona (zona_id, nombre) VALUES (2, 'PALCO');
INSERT INTO zona (zona_id, nombre) VALUES (3, 'VIP');
INSERT INTO zona (zona_id, nombre) VALUES (4, 'GENERAL');
-- Cambio: Alinea el contador de ids con el ultimo id escrito a mano
SELECT setval('zona_zona_id_seq', 4);

INSERT INTO sala (cine_id, nombre, capacidad) VALUES (1, 'Sala IMAX 1', 84);
INSERT INTO sala (cine_id, nombre, capacidad) VALUES (1, 'Sala IMAX 2', 84);
INSERT INTO sala (cine_id, nombre, capacidad) VALUES (2, 'Sala IMAX 1', 84);
INSERT INTO sala (cine_id, nombre, capacidad) VALUES (2, 'Sala IMAX 2', 84);

-- -------------------- Asientos --------------------
-- 14 asientos, filas A a la F, las primeras dos filas son VIP para la gente fina
DO $$
DECLARE
    sala_actual INT := 1;
    fila_actual INT := 1;
    asiento_actual INT := 1;
    letra_de_la_fila VARCHAR(2) := '';
    zona_del_asiento INT := 1;
BEGIN
    WHILE (sala_actual <= 4) LOOP
        fila_actual := 1;

        WHILE (fila_actual <= 6) LOOP
            letra_de_la_fila := chr(64 + fila_actual);
            asiento_actual := 1;

            IF (fila_actual <= 2) THEN
                zona_del_asiento := 3;
            ELSE
                zona_del_asiento := 1;
            END IF;

            WHILE (asiento_actual <= 14) LOOP
                INSERT INTO asiento (sala_id, zona_id, fila, numero)
                VALUES (sala_actual, zona_del_asiento, letra_de_la_fila, asiento_actual);

                asiento_actual := asiento_actual + 1;
            END LOOP;

            fila_actual := fila_actual + 1;
        END LOOP;

        sala_actual := sala_actual + 1;
    END LOOP;
END $$;

-- -------------------- Peliculas --------------------
INSERT INTO genero (nombre) VALUES ('Niños');
INSERT INTO genero (nombre) VALUES ('Animado');
INSERT INTO genero (nombre) VALUES ('Aventura');
INSERT INTO genero (nombre) VALUES ('Accion');
INSERT INTO genero (nombre) VALUES ('Terror');

INSERT INTO pelicula (titulo, sinopsis, clasificacion, duracion_min, poster_url)
VALUES ('Coyote VS. ACME',
'Después de que todos los productos fabricados por la Corporación ACME fallaran para Wile E. Coyote en su persecución del Correcaminos, el abogado Kevin Avery decide representarlo en una demanda contra ACME. Una creciente amistad entre los dos impulsará su determinación por ganar el caso al enfrentar a Buddy Crane, el intimidante jefe del antiguo bufete de Kevin, quien ahora representa a ACME.', 
'TP', 103, 'posters/coyote.png');

INSERT INTO pelicula (titulo, sinopsis, clasificacion, duracion_min, poster_url)
VALUES ('Resident Evil: Noche Cero', 
'Película basada en la saga de videojuegos de Capcom del mismo nombre. En una reinvención totalmente nueva, el mensajero médico Bryan (Austin Abrams) se ve inmerso en una carrera de acción sin descanso por la supervivencia, mientras el caos se desata a su alrededor.', 
'M18', '93', 'posters/RE.png');

INSERT INTO pelicula (titulo, sinopsis, clasificacion, duracion_min, poster_url)
VALUES ('RE: Cars 1', 
'Rayo McQueen, un audaz y presumido auto de carreras novato destinado al éxito, descubre que la vida es acerca del recorrido, no de la meta final, cuando se encuentra de pronto en el tranquilo pueblo de Radiador Springs, en la Ruta 66. Allí McQueen conoce a los peculiares personajes de este pueblo, entre ellos Doc Hudson, Mate y Sally.', 
'TP', 117, 'posters/cars.png');

INSERT INTO pelicula (titulo, sinopsis, clasificacion, duracion_min, poster_url)
VALUES ('Your Name', 
'Mitsuha, una adolescente que vive en un pequeño pueblo de Japón, sueña con escapar de su vida cotidiana y conocer una ciudad llena de oportunidades. Taki, un joven que vive en Tokio, lleva una vida completamente diferente. Un día, ambos comienzan a intercambiar cuerpos misteriosamente mientras duermen, despertando cada uno en la vida del otro. Aunque al principio intentan comprender y controlar este extraño fenómeno, poco a poco desarrollan un vínculo especial a través de mensajes y recuerdos. Sin embargo, cuando el intercambio desaparece inesperadamente, Taki emprende una búsqueda para encontrar a Mitsuha y descubrir la verdad detrás de su conexión, enfrentándose a un misterio que trasciende el tiempo y el espacio. Revive esta historia 10 años despues de su estreno en salas de cine.', 
'M12', 107, 'posters/yourName.png');

INSERT INTO pelicula (titulo, sinopsis, clasificacion, duracion_min, poster_url)
VALUES ('Shrek 25 Aniversario', 
'A 25 años de su estreno, Shrek vuelve a los cines para celebrar el aniversario de una de las películas animadas más queridas de todos los tiempos. La historia del ogro que desafió los cuentos de hadas regresa a la pantalla grande con todo su humor, emoción y personajes inolvidables, invitando a fans de siempre y nuevas generaciones a revivir una aventura que marcó a toda una época.', 
'TP', 91, 'posters/eshereck.png');

--------------------- Generos --------------------
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (1, 2);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (1, 3);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (1, 4);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (2, 4);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (2, 5);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (3, 1);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (3, 2);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (3, 3);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (4, 2);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (5, 2);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (5, 3);
INSERT INTO pelicula_genero (pelicula_id, genero_id) VALUES (5, 4);

----------------- Funciones disponibles -----------------
INSERT INTO funcion (pelicula_id, sala_id, inicio, fin) VALUES (1, 1, '2026-10-26 19:00', '2026-10-26 21:08');
INSERT INTO funcion (pelicula_id, sala_id, inicio, fin) VALUES (2, 2, '2026-10-26 18:30', '2026-10-26 20:22');
INSERT INTO funcion (pelicula_id, sala_id, inicio, fin) VALUES (3, 3, '2026-10-26 21:30', '2026-10-26 23:14');
INSERT INTO funcion (pelicula_id, sala_id, inicio, fin) VALUES (4, 4, '2026-10-27 17:00', '2026-10-27 18:38');
INSERT INTO funcion (pelicula_id, sala_id, inicio, fin) VALUES (5, 1, '2026-10-27 20:00', '2026-10-27 22:15');
INSERT INTO funcion (pelicula_id, sala_id, inicio, fin) VALUES (1, 3, '2026-10-28 19:30', '2026-10-28 21:38');
INSERT INTO funcion (pelicula_id, sala_id, inicio, fin) VALUES (2, 4, '2026-10-28 16:00', '2026-10-28 17:52');

-- empieza 1 hora despues de correr le script para probar el check in
INSERT INTO funcion (pelicula_id, sala_id, inicio, fin)
VALUES (5, 2, now() + interval '1 hour', now() + interval '3 hours 15 minutes');

--------------------- Entradas ------------------
-- Cambio: ahora en lugar de solo nombre ahora queda el id del rol fijo para evitar que se siga incrementando
INSERT INTO tipo_entrada (tipo_entrada_id, nombre) VALUES (1, 'Adulto');
INSERT INTO tipo_entrada (tipo_entrada_id, nombre) VALUES (2, 'Niño');
INSERT INTO tipo_entrada (tipo_entrada_id, nombre) VALUES (3, 'Tercera edad');
INSERT INTO tipo_entrada (tipo_entrada_id, nombre) VALUES (4, 'Estudiante');
-- Cambio: Alinea el contador de ids con el ultimo id escrito a mano
SELECT setval('tipo_entrada_tipo_entrada_id_seq', 4);

---------------------- Tarifas --------------------
-- se calcula con la combinacion de los datos de la tabla de info tarifas
DO $$
DECLARE
    zona_actual INT := 1;
    tipo_actual INT := 1;
    dia_actual INT := 0;
    precio_calculado NUMERIC(10,2) := 0;
BEGIN
    WHILE (zona_actual <= 4) LOOP
        tipo_actual := 1;

        WHILE (tipo_actual <= 4) LOOP
            dia_actual := 0;

            WHILE (dia_actual <= 6) LOOP
                IF (tipo_actual = 1) THEN
                    precio_calculado := 12.00;
                ELSIF (tipo_actual = 4) THEN
                    precio_calculado := 9.00;
                ELSE
                    precio_calculado := 8.00;
                END IF;

                IF (zona_actual = 3) THEN
                    precio_calculado := precio_calculado + 6.00;
                ELSIF (zona_actual = 2) THEN
                    precio_calculado := precio_calculado + 3.00;
                ELSIF (zona_actual = 4) THEN
                    precio_calculado := precio_calculado - 2.00;
                END IF;

                IF (dia_actual = 0 OR dia_actual = 5 OR dia_actual = 6) THEN
                    precio_calculado := precio_calculado + 2.00;
                END IF;

                INSERT INTO tarifa (zona_id, tipo_entrada_id, dia_semana, precio)
                VALUES (zona_actual, tipo_actual, dia_actual, precio_calculado);

                dia_actual := dia_actual + 1;
            END LOOP;

            tipo_actual := tipo_actual + 1;
        END LOOP;

        zona_actual := zona_actual + 1;
    END LOOP;
END $$;

-- De lunes a viernes hay 2x1 como el duo tickets visa (que en paz descanse esa bella promocion)
INSERT INTO promocion (nombre, tipo, dia_semana) VALUES ('2x1 de lunes', '2X1', 1);
INSERT INTO promocion (nombre, tipo, dia_semana) VALUES ('2x1 de martes', '2X1', 2);
INSERT INTO promocion (nombre, tipo, dia_semana) VALUES ('2x1 de miercoles', '2X1', 3);
INSERT INTO promocion (nombre, tipo, dia_semana) VALUES ('2x1 de jueves', '2X1', 4);
INSERT INTO promocion (nombre, tipo, dia_semana) VALUES ('2x1 de viernes', '2X1', 5);
-------------------- Metodos de Pago -----------------

INSERT INTO metodo_pago (nombre) VALUES ('Tarjeta de crédito');
INSERT INTO metodo_pago (nombre) VALUES ('Tarjeta de débito');
INSERT INTO metodo_pago (nombre) VALUES ('PayPal');
INSERT INTO metodo_pago (nombre) VALUES ('Billetera digital');
INSERT INTO metodo_pago (nombre) VALUES ('Transferencia');