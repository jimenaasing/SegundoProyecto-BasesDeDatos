
#Prueba de concurrencia y prevención de doble venta 
#Script automatizado con multihilos

import argparse
import os
import sys
import threading
import time

import psycopg2
from psycopg2 import errors

FUNCION_ID = 1
ASIENTO = "A1"


def conectar():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "imax"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )


def preparar(con_restriccion):
    """Crea una tabla de prueba aparte (no toca las tablas reales)."""
    con = conectar()
    with con, con.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS prueba_reserva")
        cur.execute("""
            CREATE TABLE prueba_reserva (
                id         SERIAL PRIMARY KEY,
                funcion_id INT  NOT NULL,
                asiento    TEXT NOT NULL,
                usuario    TEXT NOT NULL,
                momento    TIMESTAMPTZ DEFAULT now()
            )""")
        if con_restriccion:
            cur.execute("""
                ALTER TABLE prueba_reserva
                ADD CONSTRAINT uq_funcion_asiento UNIQUE (funcion_id, asiento)""")
    con.close()


def intentar(i, barrera, resultados):
    """Un 'cliente': su propia conexión y su propia transacción."""
    con = conectar()                 # cada hilo usa SU conexión
    try:
        barrera.wait()               # todos arrancan en el mismo instante
        try:
            with con.cursor() as cur:
                cur.execute(
                    "INSERT INTO prueba_reserva (funcion_id, asiento, usuario) "
                    "VALUES (%s, %s, %s)",
                    (FUNCION_ID, ASIENTO, f"usuario_{i}"))
            con.commit()
            resultados[i] = "EXITO"
        except errors.UniqueViolation:
            con.rollback()
            resultados[i] = "RECHAZADO (violación de unicidad)"
        except psycopg2.Error as e:
            con.rollback()
            resultados[i] = f"ERROR ({e.pgcode})"
    finally:
        con.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hilos", type=int, default=30)
    ap.add_argument("--sin-restriccion", action="store_true")
    args = ap.parse_args()

    preparar(con_restriccion=not args.sin_restriccion)

    barrera = threading.Barrier(args.hilos)
    resultados = [None] * args.hilos
    hilos = [threading.Thread(target=intentar, args=(i, barrera, resultados))
             for i in range(args.hilos)]

    t0 = time.perf_counter()
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    dur = time.perf_counter() - t0

    exitos = resultados.count("EXITO")
    rechazos = sum(1 for r in resultados if r and r.startswith("RECHAZADO"))
    errores = args.hilos - exitos - rechazos

    con = conectar()
    with con, con.cursor() as cur:
        cur.execute("SELECT count(*) FROM prueba_reserva "
                    "WHERE funcion_id = %s AND asiento = %s", (FUNCION_ID, ASIENTO))
        filas = cur.fetchone()[0]
    con.close()

    print("=" * 56)
    print(f"Modo:                 {'SIN restricción' if args.sin_restriccion else 'CON restricción UNIQUE'}")
    print(f"Solicitudes:          {args.hilos} (mismo asiento, misma función)")
    print(f"Éxitos:               {exitos}")
    print(f"Rechazos:             {rechazos}")
    print(f"Otros errores:        {errores}")
    print(f"Filas en la tabla:    {filas}")
    print(f"Duración:             {dur:.3f} s")
    print("=" * 56)

    if args.sin_restriccion:
        print("DEMO: sin restricción hubo doble venta." if filas > 1
              else "No se vio doble venta en esta corrida; repite o sube --hilos.")
        return 0
    if exitos == 1 and filas == 1 and errores == 0:
        print("RESULTADO: CORRECTO. Una sola reserva; el resto fue rechazado por la BD.")
        return 0
    print("RESULTADO: FALLO. Hay doble venta o errores inesperados.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
