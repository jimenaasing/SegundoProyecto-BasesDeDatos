-- Sirve para limpiar 
TRUNCATE TABLE boleto, pago, bloqueo_asiento, orden, funcion, pelicula_genero,
    pelicula, genero, tarifa, promocion, tipo_entrada, metodo_pago,
    asiento, sala, zona, cine, usuario, rol
RESTART IDENTITY CASCADE;