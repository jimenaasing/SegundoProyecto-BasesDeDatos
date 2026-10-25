#Base de Datos - Segundo Proyecto
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta 
import qrcode 
from decimal import Decimal, InvalidOperation
import re
import uuid
import os
import customtkinter as ctk
import psycopg2
try:
    from tkcalendar import DateEntry
except ImportError:
    DateEntry = None

COLORES = {
    "disponible": "#2e9e4f",   # verde
    "ocupado": "#7a7a7a",      # gris
    "bloqueado": "#e0b400",    # amarillo
    "seleccionado": "#2f6fdb", # azul
}
COLUMNAS_CARTELERA = 3  # tarjetas por fila
MAX_ASIENTOS = 6  # RN-04
ROLES_COMPRADORES = ("Cliente", "Taquillero")
METODOS_PAGO = ["Tarjeta de crédito", "Tarjeta de débito", "PayPal",
                "Billetera digital", "Transferencia"]
SEGUNDOS_BLOQUEO = 120  # RN-05
MIN_ANTES = 30     # RN-16: minutos antes del inicio
MIN_DESPUES = 15   # RN-16: minutos después del inicio
CARGO_SERVICIO = Decimal("1.50")   # por entrada (RN-08)
PROMO_2X1 = True                   # 1 gratis por cada 2 de la misma categoría (RN-07)
MENU_POR_ROL = {
    None:               ["cartelera", "login"],
    "Cliente":          ["cartelera","mis_entradas", "logout"],
    "Taquillero":       ["cartelera", "logout"],
    "Operador de Sala": ["cartelera", "checkin", "logout"],
    "Contador":         ["cartelera", "admin", "logout"],
    "Administrador":    ["cartelera", "admin", "logout"],
}
# Pestañas del panel que ve cada rol (RBAC)
TABS_ADMIN = {
    "Administrador": ["Reportes", "Películas", "Funciones", "Precios", "Reembolsos", "Auditoría"],
    "Contador": ["Reportes"],}
LIMPIEZA_MIN = 20  # minutos entre funciones de una misma sala


class AppCine(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cine IMAX")
        self.geometry("1280x760")
        self.minsize(1050, 650)

        self.conn_params = {
            "dbname": os.getenv("IMAX_DB_NAME", "imax"), 
            "user": os.getenv("IMAX_DB_USER", "postgres"),
            "password": os.getenv("IMAX_DB_PASSWORD", ""),
            "host": os.getenv("IMAX_DB_HOST", "localhost"),
            "port": os.getenv("IMAX_DB_PORT", "5432"),
        }
        self.cartelera_combo = {}
        self.asientos_combo = {}
        self.entradas_combo = {}
        self.pasarela_pago_combo = {}
        self.emision_combo = {}

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.bloqueo_job = None
        self.usuario_actual = None
        self.accion_pendiente = None

        hoy = datetime.now().strftime("%Y-%m-%d")
        manana = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.funciones_sim = [
            {
                "id": 1, "titulo": "Película de prueba 1",
                "sinopsis": "Sinopsis de ejemplo.", "clasificacion": "B",
                "genero": "Acción", "ubicacion": "Los Ángeles",
                "sala": "Sala IMAX 1", "fecha": hoy, "hora": "19:00",
                "filas": 8, "cols": 12,
            },
            {
                "id": 2, "titulo": "Película de prueba 2",
                "sinopsis": "Otra sinopsis de ejemplo.", "clasificacion": "A",
                "genero": "Drama", "ubicacion": "San José",
                "sala": "Sala IMAX 2", "fecha": manana, "hora": "21:30",
                "filas": 6, "cols": 10,
            },
        ]
        self.tarifas_sim = {
            "Adulto": Decimal("12.00"),
            "Niño": Decimal("8.00"),
            "Tercera edad": Decimal("8.00"),
            "Estudiante": Decimal("9.00"),
        }
        self.boletos_sim = {}
        self.log_acceso = []
        self.audit_sim = []

        self.crear_sidebar()
        self.crear_area_principal()

#------------------------ INFRAESTRUCTURA ------------------------

#--------- Esto devuelve None cuando hay error de BD ---------
    def consultar(self, sql, params=None):
        conn = None
        try:
            conn = psycopg2.connect(**self.conn_params)
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return cur.fetchall()
        except psycopg2.Error as e:
            messagebox.showerror("Error de base de datos", str(e))
            return None
        finally:
            if conn:
                conn.close()

    def crear_area_principal(self):
        self.main = ctk.CTkFrame(self)
        self.main.grid(row=0, column=1, sticky="nsew")
        self.main.grid_rowconfigure(0, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        self.pantallas = {
        "cartelera": ctk.CTkFrame(self.main),
        "asientos": ctk.CTkFrame(self.main),
        "tarifas": ctk.CTkFrame(self.main),
        "pago": ctk.CTkFrame(self.main),
        "confirmacion": ctk.CTkFrame(self.main),
        "checkin": ctk.CTkFrame(self.main),
        "login": ctk.CTkFrame(self.main),
        "admin": ctk.CTkFrame(self.main),
        "mis_entradas": ctk.CTkFrame(self.main),
       
    }
        self.construir_cartelera()
        self.mostrar_pantalla("cartelera")  #Esta es la pantalla de inicio

    def mostrar_pantalla(self, nombre):
        for p in self.pantallas.values():
            p.grid_forget()
        self.pantallas[nombre].grid(row=0, column=0, sticky="nsew")

    def cargar_funciones(self):
        # TODO: reemplazar por un SELECT (solo funciones activas y futuras, RN-01)
        #return [
            #{"id": 1, "titulo": "Película de prueba 1", "sinopsis": "Sinopsis de ejemplo.",
            #"clasificacion": "B", "genero": "Acción", "ubicacion": "Los Ángeles",
            #"sala": "Sala IMAX 1", "fecha": "2026-10-25", "hora": "19:00", "filas": 8, "cols": 12},
            #{"id": 2, "titulo": "Película de prueba 2", "sinopsis": "Otra sinopsis de ejemplo.",
             #"clasificacion": "A", "genero": "Drama", "ubicacion": "San José",
            #"sala": "Sala IMAX 2", "fecha": "2026-10-26", "hora": "21:30", "filas": 6, "cols": 10},
            # TODO: BD, SELECT de funciones activas y futuras (RN-01)
        return list(self.funciones_sim)

    def cargar_tarifas(self, funcion_id):
        # TODO: BD, matriz de precios según día, horario y tipo de asiento
        return dict(self.tarifas_sim)

    def cargar_estados_asientos(self, funcion_id):
        # TODO: BD, estado real de cada asiento de esa función
        estados = {"A1": "ocupado", "A2": "ocupado", "C5": "bloqueado", "C6": "bloqueado"}
        for b in self.boletos_sim.values():
            if b["funcion_id"] == funcion_id and not b.get("reembolsado"):
                estados[b["asiento"]] = "ocupado"
        return estados  

    def construir_cartelera(self):
        f = self.pantallas["cartelera"]
        f.grid_columnconfigure(0, weight=1)
        f.grid_rowconfigure(1, weight=1)

        filtros = ctk.CTkFrame(f)
        filtros.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        self.cb_ubicacion = ctk.CTkComboBox(filtros, values=["Todas", "Los Ángeles", "San José"],
                                        command=lambda _: self.refrescar_cartelera())
        self.cb_ubicacion.pack(side="left", padx=5)
        self.cb_genero = ctk.CTkComboBox(filtros, values=["Todos", "Acción", "Drama"],
                                     command=lambda _: self.refrescar_cartelera())
        self.cb_genero.pack(side="left", padx=5)
        self.ent_fecha = ctk.CTkEntry(filtros, placeholder_text="Fecha AAAA-MM-DD")
        self.ent_fecha.pack(side="left", padx=5)
        self.ent_fecha.bind("<KeyRelease>", lambda e: self.refrescar_cartelera())

        self.lista = ctk.CTkScrollableFrame(f)
        self.lista.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.refrescar_cartelera()

    def refrescar_cartelera(self):
        for w in self.lista.winfo_children():
            w.destroy()
        for c in range(COLUMNAS_CARTELERA):
            self.lista.grid_columnconfigure(c, weight=1, uniform="tarjeta")

        ub, gen = self.cb_ubicacion.get(), self.cb_genero.get()
        fecha = self.ent_fecha.get().strip()

        funciones = []
        for fn in self.cargar_funciones():
            if ub != "Todas" and fn["ubicacion"] != ub: continue
            if gen != "Todos" and fn["genero"] != gen: continue
            if fecha and not fn["fecha"].startswith(fecha): continue
            funciones.append(fn)

        if not funciones:
            ctk.CTkLabel(self.lista, text="No hay funciones con esos filtros.").grid(
                row=0, column=0, columnspan=COLUMNAS_CARTELERA, pady=20)
            return

        for i, fn in enumerate(funciones):
            fila, col = divmod(i, COLUMNAS_CARTELERA)
            tarjeta = ctk.CTkFrame(self.lista, corner_radius=10, border_width=1)
            tarjeta.grid(row=fila, column=col, padx=10, pady=10, sticky="nsew")

            ctk.CTkLabel(tarjeta, text=fn["titulo"], font=("Arial", 16, "bold"),
                         wraplength=220, justify="left").pack(anchor="w", padx=12, pady=(12, 2))
            ctk.CTkLabel(tarjeta, text=f'Clasificación {fn["clasificacion"]} · {fn["genero"]}',
                         text_color="gray").pack(anchor="w", padx=12)
            ctk.CTkLabel(tarjeta, text=fn["sinopsis"], wraplength=220,
                         justify="left").pack(anchor="w", padx=12, pady=8)
            ctk.CTkLabel(tarjeta, text=f'{fn["ubicacion"]} · {fn["sala"]}\n{fn["fecha"]} · {fn["hora"]}',
                         justify="left").pack(anchor="w", padx=12)
            ctk.CTkButton(tarjeta, text="Elegir",
                          command=lambda x=fn: self.elegir_funcion(x)).pack(
                fill="x", padx=12, pady=12)

        
    def cargar_estados_asientos(self, funcion_id):
        # TODO: reemplazar por SELECT a la BD: estado de cada asiento de esa función
        return {"A1": "ocupado", "A2": "ocupado", "C5": "bloqueado", "C6": "bloqueado"}

    def elegir_funcion(self, funcion):
        self.funcion_elegida = funcion
        self.asientos_elegidos = set()
        self.construir_mapa_asientos()
        self.mostrar_pantalla("asientos")

    def construir_mapa_asientos(self):
        f = self.pantallas["asientos"]
        for w in f.winfo_children():
            w.destroy()
        fn = self.funcion_elegida

        ctk.CTkLabel(f, text=f'{fn["titulo"]} · {fn["sala"]} · {fn["hora"]}',
                    font=("Arial", 20, "bold")).pack(pady=10)
        ctk.CTkLabel(f, text="PANTALLA", fg_color="#444444", width=500).pack(pady=5)

        malla = ctk.CTkFrame(f)
        malla.pack(pady=10)
        estados = self.cargar_estados_asientos(fn["id"])
        self.botones_asientos = {}
        for r in range(fn["filas"]):
            for c in range(fn["cols"]):
                codigo = f"{chr(65 + r)}{c + 1}"
                estado = estados.get(codigo, "disponible")
                b = ctk.CTkButton(malla, text=codigo, width=42, height=34,
                                fg_color=COLORES[estado], hover=False,
                                command=lambda cod=codigo: self.click_asiento(cod))
                b.grid(row=r, column=c, padx=2, pady=2)
                if estado != "disponible":
                    b.configure(state="disabled")
                self.botones_asientos[codigo] = b

        leyenda = ctk.CTkFrame(f)
        leyenda.pack(pady=5)
        for nombre, color in COLORES.items():
            ctk.CTkLabel(leyenda, text=f"  {nombre}  ", fg_color=color,
                        corner_radius=6).pack(side="left", padx=4)

        self.lbl_resumen = ctk.CTkLabel(f, text="Asientos: ninguno")
        self.lbl_resumen.pack(pady=5)
        fila = ctk.CTkFrame(f)
        fila.pack(pady=5)
        ctk.CTkButton(fila, text="Volver",
                    command=lambda: self.mostrar_pantalla("cartelera")).pack(side="left", padx=5)
        ctk.CTkButton(fila, text="Continuar", command=self.continuar_a_tarifas).pack(side="left", padx=5)

    def click_asiento(self, codigo):
        if codigo in self.asientos_elegidos:
            self.asientos_elegidos.remove(codigo)
            color = COLORES["disponible"]
        else:
            if len(self.asientos_elegidos) >= MAX_ASIENTOS:
                messagebox.showwarning("Límite", f"Máximo {MAX_ASIENTOS} asientos por compra.")
                return
            self.asientos_elegidos.add(codigo)
            color = COLORES["seleccionado"]
        self.botones_asientos[codigo].configure(fg_color=color)
        lista = ", ".join(sorted(self.asientos_elegidos)) or "ninguno"
        self.lbl_resumen.configure(text=f"Asientos: {lista}")

    def continuar_a_tarifas(self):
        if not self.asientos_elegidos:
            messagebox.showinfo("Selección", "Elige al menos un asiento.")
            return
        # TODO: aquí se pide a la BD el bloqueo de 2 min (RN-05); si falla hay que refrescar el mapa
        self.iniciar_bloqueo()
        self.construir_tarifas()
        self.mostrar_pantalla("tarifas")

        if self.rol_actual() not in ROLES_COMPRADORES:
            if self.usuario_actual is None:
                messagebox.showinfo("Inicio de sesión",
                                    "Inicia sesión para continuar con la compra.")
                self.accion_pendiente = "compra"
                self.abrir_login()
            else:
                messagebox.showwarning("Permisos", "Tu rol no puede comprar entradas.")
            return

    def crear_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        ctk.CTkLabel(self.sidebar, text="Cine IMAX",
                     font=("Arial", 22, "bold")).pack(padx=20, pady=20)

        self.menu = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.menu.pack()
        self.lbl_timer = ctk.CTkLabel(self.sidebar, text="", font=("Arial", 16, "bold"))
        self.lbl_timer.pack(padx=20, pady=20)

        self.actualizar_menu()

    def cargar_tarifas(self, funcion_id):
        # TODO: reemplazar por SELECT a la matriz de precios (según día, horario y tipo de asiento)
        return {
            "Adulto": Decimal("12.00"),
            "Niño": Decimal("8.00"),
            "Tercera edad": Decimal("8.00"),
            "Estudiante": Decimal("9.00"),
        }

    def construir_tarifas(self):
        f = self.pantallas["tarifas"]
        for w in f.winfo_children():
            w.destroy()
        fn = self.funcion_elegida
        self.tarifas = self.cargar_tarifas(fn["id"])

        ctk.CTkLabel(f, text="Tipo de entrada", font=("Arial", 20, "bold")).pack(pady=10)
        ctk.CTkLabel(f, text=f'{fn["titulo"]} · {fn["sala"]} · {fn["fecha"]} {fn["hora"]}').pack()

        lista = ctk.CTkFrame(f)
        lista.pack(pady=15)
        self.tipo_vars = {}
        for i, codigo in enumerate(sorted(self.asientos_elegidos)):
            ctk.CTkLabel(lista, text=f"Asiento {codigo}", width=100).grid(
                row=i, column=0, padx=10, pady=5)
            var = ctk.StringVar(value="Adulto")
            self.tipo_vars[codigo] = var
            ctk.CTkComboBox(lista, values=list(self.tarifas.keys()), variable=var,
                            state="readonly",
                            command=lambda _: self.recalcular_total()).grid(
                row=i, column=1, padx=10, pady=5)

        ctk.CTkLabel(f, text="Las tarifas de niño, tercera edad y estudiante se verifican "
                             "con documento en la puerta (RN-06).",
                     text_color="gray").pack(pady=5)

        self.lbl_total = ctk.CTkLabel(f, text="", justify="left", font=("Arial", 14))
        self.lbl_total.pack(pady=10)

        fila = ctk.CTkFrame(f)
        fila.pack(pady=5)
        ctk.CTkButton(fila, text="Volver",
                      command=lambda: self.mostrar_pantalla("asientos")).pack(side="left", padx=5)
        ctk.CTkButton(fila, text="Continuar al pago",
                      command=self.continuar_a_pago).pack(side="left", padx=5)
        self.recalcular_total()

    def calcular_total(self):
        # Devuelve subtotal, descuento, cargo y total
        conteo = {}
        for var in self.tipo_vars.values():
            conteo[var.get()] = conteo.get(var.get(), 0) + 1

        subtotal = sum(self.tarifas[t] * n for t, n in conteo.items())
        descuento = Decimal("0")
        if PROMO_2X1:
            for t, n in conteo.items():
                descuento += self.tarifas[t] * (n // 2)   # 1 gratis por cada par de la misma categoría
        cargo = CARGO_SERVICIO * len(self.tipo_vars)
        total = subtotal - descuento + cargo
        return subtotal, descuento, cargo, total

    def recalcular_total(self):
        subtotal, descuento, cargo, total = self.calcular_total()
        self.lbl_total.configure(text=(
            f"Subtotal: ${subtotal:.2f}\n"
            f"Descuento 2x1: -${descuento:.2f}\n"
            f"Cargo por servicio: ${cargo:.2f}\n"
            f"TOTAL: ${total:.2f}"))

    def continuar_a_pago(self):
        subtotal, descuento, cargo, total = self.calcular_total()
        self.compra_actual = {
            "funcion": self.funcion_elegida,
            "asientos": {c: v.get() for c, v in self.tipo_vars.items()},
            "subtotal": subtotal, "descuento": descuento,
            "cargo": cargo, "total": total,
        }
        self.construir_pago()
        self.mostrar_pantalla("pago")
  
#----- Para iniciar el temporizador de bloqueo de asientos y manejar su expiración -----
    def iniciar_bloqueo(self):
        self.cancelar_bloqueo()
        self.segundos_restantes = SEGUNDOS_BLOQUEO
        self.tick_bloqueo()

    def tick_bloqueo(self):
        m, s = divmod(self.segundos_restantes, 60)
        self.lbl_timer.configure(text=f"Bloqueo: {m}:{s:02d}")
        if self.segundos_restantes <= 0:
            self.bloqueo_job = None
            self.expirar_bloqueo()
            return
        self.segundos_restantes -= 1
        self.bloqueo_job = self.after(1000, self.tick_bloqueo)

    def cancelar_bloqueo(self):
        if self.bloqueo_job:
            self.after_cancel(self.bloqueo_job)
            self.bloqueo_job = None
        self.lbl_timer.configure(text="")

    def expirar_bloqueo(self):
        messagebox.showwarning("Tiempo agotado",
                               "Se agotó el tiempo y los asientos fueron liberados.")
        self.liberar_asientos()
        self.mostrar_pantalla("cartelera")

    def liberar_asientos(self):
        self.cancelar_bloqueo()
        # TODO: BD, liberar los asientos bloqueados de esta compra
        self.asientos_elegidos = set()
        self.compra_actual = None

    def volver_a_cartelera(self):
        self.liberar_asientos()
        self.mostrar_pantalla("cartelera")


    def construir_pago(self):
        f = self.pantallas["pago"]
        for w in f.winfo_children():
            w.destroy()
        c = self.compra_actual
        fn = c["funcion"]

        ctk.CTkLabel(f, text="Pago seguro (simulado)", font=("Arial", 20, "bold")).pack(pady=10)

        resumen = ctk.CTkFrame(f)
        resumen.pack(pady=5, padx=20, fill="x")
        asientos = ", ".join(f"{a} ({t})" for a, t in sorted(c["asientos"].items()))
        ctk.CTkLabel(resumen, justify="left", anchor="w", wraplength=700, text=(
            f'{fn["titulo"]} · {fn["sala"]} · {fn["fecha"]} {fn["hora"]}\n'
            f'Asientos: {asientos}\n'
            f'Subtotal: ${c["subtotal"]:.2f}   Descuento: -${c["descuento"]:.2f}   '
            f'Cargo: ${c["cargo"]:.2f}\n'
            f'TOTAL: ${c["total"]:.2f}')).pack(padx=15, pady=10, anchor="w")

        fila_metodo = ctk.CTkFrame(f)
        fila_metodo.pack(pady=10)
        ctk.CTkLabel(fila_metodo, text="Método de pago:").pack(side="left", padx=5)
        self.metodo_var = ctk.StringVar(value=METODOS_PAGO[0])
        ctk.CTkComboBox(fila_metodo, values=METODOS_PAGO, variable=self.metodo_var,
                        state="readonly", width=200,
                        command=self.actualizar_campos_pago).pack(side="left", padx=5)

        tarjeta = ctk.CTkFrame(f)
        tarjeta.pack(pady=5)
        self.ent_numero = ctk.CTkEntry(tarjeta, width=260, placeholder_text="Número de tarjeta")
        self.ent_nombre = ctk.CTkEntry(tarjeta, width=260, placeholder_text="Nombre del titular")
        self.ent_venc = ctk.CTkEntry(tarjeta, width=125, placeholder_text="MM/AA")
        self.ent_cvv = ctk.CTkEntry(tarjeta, width=125, placeholder_text="CVV", show="*")
        self.ent_numero.grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        self.ent_nombre.grid(row=1, column=0, columnspan=2, padx=10, pady=5)
        self.ent_venc.grid(row=2, column=0, padx=10, pady=5)
        self.ent_cvv.grid(row=2, column=1, padx=10, pady=5)
        self.campos_tarjeta = [self.ent_numero, self.ent_nombre, self.ent_venc, self.ent_cvv]

        sim = ctk.CTkFrame(f)
        sim.pack(pady=10)
        ctk.CTkLabel(sim, text="Resultado simulado de la pasarela (solo demo):").pack(
            side="left", padx=5)
        self.resultado_var = ctk.StringVar(value="Aprobado")
        ctk.CTkSegmentedButton(sim, values=["Aprobado", "Rechazado"],
                               variable=self.resultado_var).pack(side="left", padx=5)

        botones = ctk.CTkFrame(f)
        botones.pack(pady=10)
        ctk.CTkButton(botones, text="Volver",
                      command=lambda: self.mostrar_pantalla("tarifas")).pack(side="left", padx=5)
        ctk.CTkButton(botones, text="Pagar", command=self.pagar).pack(side="left", padx=5)
        self.actualizar_campos_pago()

    def actualizar_campos_pago(self, _=None):
        es_tarjeta = "Tarjeta" in self.metodo_var.get()
        for e in self.campos_tarjeta:
            e.configure(state="normal" if es_tarjeta else "disabled")

    def validar_datos_pago(self):
        # Devuelve (ok, últimos 4 dígitos). Para métodos sin tarjeta no se valida nada.
        if "Tarjeta" not in self.metodo_var.get():
            return True, None
        numero = self.ent_numero.get().replace(" ", "")
        if not (numero.isdigit() and 13 <= len(numero) <= 19):
            messagebox.showwarning("Pago", "Número de tarjeta inválido.")
            return False, None
        if not self.ent_nombre.get().strip():
            messagebox.showwarning("Pago", "Escribe el nombre del titular.")
            return False, None
        if not re.fullmatch(r"(0[1-9]|1[0-2])/\d{2}", self.ent_venc.get().strip()):
            messagebox.showwarning("Pago", "La fecha debe tener el formato MM/AA.")
            return False, None
        cvv = self.ent_cvv.get().strip()
        if not (cvv.isdigit() and len(cvv) in (3, 4)):
            messagebox.showwarning("Pago", "CVV inválido.")
            return False, None
        return True, numero[-4:]

    def pagar(self):
        ok, ultimos4 = self.validar_datos_pago()
        if not ok:
            return
        metodo = self.metodo_var.get()
        # RN-09: el CVV y el número completo no se guardan; se borran de la pantalla
        if "Tarjeta" in metodo:
            for e in self.campos_tarjeta:
                e.delete(0, "end")
        if self.resultado_var.get() == "Aprobado":
            self.pago_aprobado(metodo, ultimos4)
        else:
            self.pago_rechazado()

    def pago_aprobado(self, metodo, ultimos4):
        self.cancelar_bloqueo()
        c = self.compra_actual
        c["metodo"] = metodo
        c["ultimos4"] = ultimos4
        # RN-11 y RN-12: los códigos se crean solo tras la aprobación, uno por boleto
        c["boletos"] = {asiento: str(uuid.uuid4()) for asiento in c["asientos"]}

        # Registro de boletos (lo leen check-in, reportes y reembolsos)
        precio = (c["total"] / len(c["asientos"])).quantize(Decimal("0.01"))
        for asiento, codigo in c["boletos"].items():
            self.boletos_sim[codigo] = {
                "funcion_id": c["funcion"]["id"], "asiento": asiento,
                "usado": False, "reembolsado": False,
                "precio": precio, "metodo": metodo, "momento": datetime.now(),
                "usuario": self.usuario_actual["usuario"],
                "tipo": c["asientos"][asiento] 
                }
        print("Boletos registrados:", len(self.boletos_sim))   # línea temporal de prueba

        # TODO: BD, en UNA sola transacción: registrar el pago, pasar los asientos
        # de "bloqueado" a "vendido", crear los boletos con su código y escribir los logs.
        # COMMIT si todo sale bien, ROLLBACK si algo falla.
        self.construir_confirmacion()
        self.mostrar_pantalla("confirmacion")

    def pago_rechazado(self):
        # RN-10: no se cobra y los asientos se liberan de inmediato
        funcion = self.funcion_elegida
        messagebox.showerror("Pago rechazado",
                             "La pasarela rechazó el pago. Los asientos fueron liberados.")
        self.liberar_asientos()   # TODO: BD, registrar el intento fallido en transaccion_log
        self.elegir_funcion(funcion)   # recarga el mapa con los estados actualizados


#--- #Este método genera el código QR usando la librería qrcode y PIL, y lo devuelve como una imagen ---
    def generar_qr_pil(self, texto):
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(texto)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").get_image()

    def construir_confirmacion(self):
        f = self.pantallas["confirmacion"]
        for w in f.winfo_children():
            w.destroy()
        c = self.compra_actual

        ctk.CTkLabel(f, text="¡Compra exitosa!", font=("Arial", 24, "bold")).pack(pady=(20, 5))
        ctk.CTkLabel(f, text=f'Total pagado: ${c["total"]:.2f} · {c["metodo"]}'
                             + (f' terminada en {c["ultimos4"]}' if c["ultimos4"] else "")
                     ).pack()

        asientos = sorted(c["boletos"].keys())
        self.boleto_var = ctk.StringVar(value=asientos[0])
        if len(asientos) > 1:
            ctk.CTkSegmentedButton(f, values=asientos, variable=self.boleto_var,
                                   command=self.mostrar_boleto).pack(pady=10)

        self.tarjeta_boleto = ctk.CTkFrame(f, corner_radius=12, border_width=1)
        self.tarjeta_boleto.pack(pady=10, padx=20)

        botones = ctk.CTkFrame(f)
        botones.pack(pady=10)
        ctk.CTkButton(botones, text="Guardar QR",
                      command=self.guardar_qr).pack(side="left", padx=5)
        ctk.CTkButton(botones, text="Volver a la cartelera",
                      command=self.terminar_compra).pack(side="left", padx=5)

        self.mostrar_boleto(asientos[0])

        ctk.CTkButton(botones, text="Copiar código", #botón para copiar el código y poder pegarlo en la puerta durante la demo (junto a “Guardar QR”):
            command=self.copiar_codigo).pack(side="left", padx=5)
    
    def copiar_codigo(self):
            codigo = self.compra_actual["boletos"][self.boleto_var.get()]
            self.clipboard_clear()
            self.clipboard_append(codigo)

#----
    def abrir_checkin(self):
        if not self.tiene_acceso("checkin"):
            messagebox.showwarning("Permisos", "No tienes permiso para esta pantalla.")
            return

        self.construir_checkin()
        self.mostrar_pantalla("checkin")

    def construir_checkin(self):
        f = self.pantallas["checkin"]
        for w in f.winfo_children():
            w.destroy()

        ctk.CTkLabel(f, text="Control de acceso", font=("Arial", 22, "bold")).pack(pady=10)

        cfg = ctk.CTkFrame(f)
        cfg.pack(pady=5, padx=20, fill="x")
        self.checkin_funciones = {
            f'{fn["titulo"]} · {fn["sala"]} · {fn["fecha"]} {fn["hora"]}': fn
            for fn in self.cargar_funciones()}
        nombres = list(self.checkin_funciones.keys())
        ctk.CTkLabel(cfg, text="Función de esta puerta:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.cb_func_puerta = ctk.CTkComboBox(cfg, values=nombres, width=420, state="readonly")
        self.cb_func_puerta.set(nombres[0])
        self.cb_func_puerta.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(cfg, text="Puerta / dispositivo:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.ent_puerta = ctk.CTkEntry(cfg, width=200)
        self.ent_puerta.insert(0, "Puerta 1")
        self.ent_puerta.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(cfg, text="Fecha y hora actual (demo):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.ent_ahora = ctk.CTkEntry(cfg, width=200)
        self.ent_ahora.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.ent_ahora.grid(row=2, column=1, padx=10, pady=5, sticky="w")

        escaneo = ctk.CTkFrame(f)
        escaneo.pack(pady=15)
        self.ent_codigo = ctk.CTkEntry(escaneo, width=420, placeholder_text="Escanea o pega el código del QR")
        self.ent_codigo.pack(side="left", padx=5)
        self.ent_codigo.bind("<Return>", lambda e: self.validar_entrada())
        ctk.CTkButton(escaneo, text="Validar", command=self.validar_entrada).pack(side="left", padx=5)

        self.lbl_resultado = ctk.CTkLabel(f, text="", font=("Arial", 22, "bold"))
        self.lbl_resultado.pack(pady=10)

        ctk.CTkLabel(f, text="Últimos intentos", text_color="gray").pack()
        self.txt_log = ctk.CTkTextbox(f, width=800, height=200, state="disabled")
        self.txt_log.pack(pady=5)
        self.refrescar_log()

    def validar_entrada(self):
        codigo = self.ent_codigo.get().strip()
        if not codigo:
            return
        try:
            ahora = datetime.strptime(self.ent_ahora.get().strip(), "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showwarning("Fecha", "Usa el formato AAAA-MM-DD HH:MM.")
            return
        fn_puerta = self.checkin_funciones[self.cb_func_puerta.get()]

        ok, mensaje = self.evaluar_entrada(codigo, fn_puerta, ahora)
        self.registrar_acceso(codigo, ok, mensaje)
        self.lbl_resultado.configure(text=("✅ " if ok else "❌ ") + mensaje,
                                     text_color="#2e9e4f" if ok else "#d93a3a")
        self.ent_codigo.delete(0, "end")

    def evaluar_entrada(self, codigo, fn_puerta, ahora):
        # TODO: BD, esta lógica debe vivir en la base de datos (función o procedimiento
        # que reciba código, función y hora, y devuelva el resultado).
        b = self.boletos_sim.get(codigo)
        if b is None:
            return False, "Código no válido"
        if b["usado"]:
            return False, "Entrada ya utilizada"                     # RN-14
        if b["funcion_id"] != fn_puerta["id"]:
            return False, "Entrada de otra función"                  # RN-15
        inicio = datetime.strptime(f'{fn_puerta["fecha"]} {fn_puerta["hora"]}', "%Y-%m-%d %H:%M")
        if ahora < inicio - timedelta(minutes=MIN_ANTES):
            return False, f"Muy temprano: el acceso abre {MIN_ANTES} min antes"   # RN-16
        if ahora > inicio + timedelta(minutes=MIN_DESPUES):
            return False, f"Fuera de tiempo: el acceso cierra {MIN_DESPUES} min después"
        if b.get("reembolsado"):
            return False, "Entrada anulada (reembolsada)" #Revisaaaar
        b["usado"] = True
        return True, f'Acceso permitido · Asiento {b["asiento"]}'
    
    
    def registrar_acceso(self, codigo, ok, mensaje):
        # TODO: BD, INSERT en acceso_puerta_log
        self.log_acceso.append({
            "momento": datetime.now(), "codigo": codigo,
            "puerta": self.ent_puerta.get().strip(),
            "resultado": "exitoso" if ok else f"rechazado ({mensaje})"})
        self.refrescar_log()

    def refrescar_log(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        for r in reversed(self.log_acceso[-15:]):
            self.txt_log.insert("end", f'{r["momento"]:%H:%M:%S} · {r["puerta"]} · '
                                       f'{r["codigo"][:8]}… · {r["resultado"]}\n')
        self.txt_log.configure(state="disabled")

#-----
    def mostrar_boleto(self, asiento):
        codigo = self.compra_actual["boletos"][asiento]
        self.dibujar_boleto(self.tarjeta_boleto, codigo)

    def guardar_qr(self):
        asiento = self.boleto_var.get()
        codigo = self.compra_actual["boletos"][asiento]
        ruta = filedialog.asksaveasfilename(defaultextension=".png",
                                            initialfile=f"entrada_{asiento}.png",
                                            filetypes=[("Imagen PNG", "*.png")])
        if ruta:
            self.generar_qr_pil(codigo).save(ruta)

    def terminar_compra(self):
        self.compra_actual = None
        self.asientos_elegidos = set()
        self.mostrar_pantalla("cartelera")

#----- Login y administración de usuarios -----
    def rol_actual(self):
        return self.usuario_actual["rol"] if self.usuario_actual else None

    def tiene_acceso(self, clave):
        return clave in MENU_POR_ROL[self.rol_actual()]

    def autenticar(self, email, clave):
        # La verificación del hash la hace PostgreSQL; la contraseña nunca se compara en Python
        filas = self.consultar(
            "SELECT u.usuario_id, u.nombre, r.nombre "
            "FROM usuario u JOIN rol r ON r.rol_id = u.rol_id "
            "WHERE lower(u.email) = lower(%s) AND u.activo "
            "AND u.password_hash = crypt(%s, u.password_hash)",
            (email, clave))
        if filas is None:
            return "ERROR"          # falló la BD, no es contraseña incorrecta
        if not filas:
            return None
        uid, nombre, rol = filas[0]
        return {"usuario_id": uid, "usuario": email.lower(), "nombre": nombre, "rol": rol}

    def actualizar_menu(self):
        for w in self.menu.winfo_children():
            w.destroy()
        if self.usuario_actual:
            texto = f'{self.usuario_actual["usuario"]}\n{self.rol_actual()}'
        else:
            texto = "Invitado"
        ctk.CTkLabel(self.menu, text=texto, text_color="gray").pack(padx=20, pady=(0, 10))

        botones = {
            "cartelera": ("Cartelera", "volver_a_cartelera"),
            "checkin": ("Check-in (puerta)", "abrir_checkin"),
            "login": ("Iniciar sesión", "abrir_login"),
            "logout": ("Cerrar sesión", "cerrar_sesion"),
            "admin": ("Panel de administración", "abrir_admin"),
            "mis_entradas": ("Mis entradas", "abrir_mis_entradas"),
        }
        for clave in MENU_POR_ROL[self.rol_actual()]:
            texto_boton, nombre_metodo = botones[clave]
            comando = getattr(self, nombre_metodo, None)
            if comando is None:
                continue
            ctk.CTkButton(self.menu, text=texto_boton, command=comando).pack(padx=20, pady=5)

    def abrir_login(self):
        f = self.pantallas["login"]
        for w in f.winfo_children():
            w.destroy()
        caja = ctk.CTkFrame(f)
        caja.place(relx=0.5, rely=0.35, anchor="center")

        ctk.CTkLabel(caja, text="Iniciar sesión", font=("Arial", 22, "bold")).pack(padx=40, pady=(20, 10))
        self.ent_usuario = ctk.CTkEntry(caja, width=260, placeholder_text="Usuario")
        self.ent_usuario.pack(padx=40, pady=5)
        self.ent_clave = ctk.CTkEntry(caja, width=260, placeholder_text="Contraseña", show="*")
        self.ent_clave.pack(padx=40, pady=5)
        self.ent_clave.bind("<Return>", lambda e: self.intentar_login())
        self.lbl_login_error = ctk.CTkLabel(caja, text="", text_color="#d93a3a")
        self.lbl_login_error.pack(pady=5)

        fila = ctk.CTkFrame(caja, fg_color="transparent")
        fila.pack(padx=40, pady=(5, 20))
        ctk.CTkButton(fila, text="Cancelar", width=120,
                      command=self.cancelar_login).pack(side="left", padx=5)
        ctk.CTkButton(fila, text="Ingresar", width=120,
                      command=self.intentar_login).pack(side="left", padx=5)
        self.mostrar_pantalla("login")

    def cancelar_login(self):
        self.accion_pendiente = None
        self.mostrar_pantalla("cartelera")

    def intentar_login(self):
        email = self.ent_usuario.get().strip()
        datos = self.autenticar(email, self.ent_clave.get())
        if datos == "ERROR":
            return
        if datos is None:
            self.lbl_login_error.configure(text="Correo o contraseña incorrectos.")
            self.ent_clave.delete(0, "end")
            return
        rol = datos["rol"]
        if rol not in MENU_POR_ROL:
            self.lbl_login_error.configure(
                text=f'El rol "{rol}" no está configurado en la aplicación.')
            return

        self.usuario_actual = datos
        self.actualizar_menu()

        if self.accion_pendiente == "compra" and rol in ROLES_COMPRADORES:
            self.accion_pendiente = None
            self.mostrar_pantalla("asientos")   
            return

        self.accion_pendiente = None
        self.liberar_asientos()
        if rol == "Operador de Sala":
            self.abrir_checkin()
        else:
            self.mostrar_pantalla("cartelera")

#---------------
    def armar_funcion(self, fid, pelicula_id, sala_id, fecha, hora):
            p = next(x for x in self.peliculas_sim if x["id"] == pelicula_id)
            s = next(x for x in self.salas_sim if x["id"] == sala_id)
            return {"id": fid, "pelicula_id": p["id"], "sala_id": s["id"],
                    "titulo": p["titulo"], "sinopsis": p["sinopsis"],
                    "clasificacion": p["clasificacion"], "genero": p["genero"],
                    "duracion": p["duracion"], "ubicacion": s["ubicacion"],
                    "sala": s["nombre"], "filas": s["filas"], "cols": s["cols"],
                    "fecha": fecha, "hora": hora}

    def registrar_auditoria(self, accion, detalle):
            # TODO: BD, INSERT en admin_operacion_audit (fecha, hora, IP, rol y usuario)
            self.audit_sim.append({
                "momento": datetime.now(), "usuario": self.usuario_actual["usuario"],
                "rol": self.rol_actual(), "ip": "127.0.0.1",
                "accion": accion, "detalle": detalle})

    def llenar_textbox(self, caja, texto):
            caja.configure(state="normal")
            caja.delete("1.0", "end")
            caja.insert("end", texto)
            caja.configure(state="disabled")

    def abrir_admin(self):
            if not self.tiene_acceso("admin"):
                messagebox.showwarning("Permisos", "No tienes permiso para esta pantalla.")
                return
            f = self.pantallas["admin"]
            for w in f.winfo_children():
                w.destroy()
            ctk.CTkLabel(f, text="Panel de administración",
                         font=("Arial", 22, "bold")).pack(pady=10)
            self.tabs = ctk.CTkTabview(f)
            self.tabs.pack(fill="both", expand=True, padx=10, pady=10)
            constructores = {
                "Reportes": self.tab_reportes, "Películas": self.tab_peliculas,
                "Funciones": self.tab_funciones, "Precios": self.tab_precios,
                "Reembolsos": self.tab_reembolsos, "Auditoría": self.tab_auditoria}
            for nombre in TABS_ADMIN[self.rol_actual()]:
                    self.tabs.add(nombre)
                    constructores[nombre](self.tabs.tab(nombre))
                    self.mostrar_pantalla("admin")

    def recargar_admin(self, pestana):
            self.abrir_admin()
            self.tabs.set(pestana)

    def texto_reportes(self):
            activos = [b for b in self.boletos_sim.values() if not b.get("reembolsado")]
            fn_por_id = {fn["id"]: fn for fn in self.funciones_sim}

            L = ["OCUPACIÓN Y RECAUDACIÓN POR FUNCIÓN"]
            for fn in self.funciones_sim:
                cap = fn["filas"] * fn["cols"]
                mios = [b for b in activos if b["funcion_id"] == fn["id"]]
                ingresos = sum((b["precio"] for b in mios), Decimal("0"))
                L.append(f'  {fn["titulo"]} · {fn["fecha"]} {fn["hora"]}: '
                         f'{len(mios)}/{cap} asientos ({len(mios) / cap:.1%}) · ${ingresos:.2f}')

            L += ["", "TOP 5 PELÍCULAS (ÚLTIMOS 7 DÍAS)"]
            desde = datetime.now() - timedelta(days=7)
            conteo = {}
            for b in activos:
                if b["momento"] >= desde:
                    t = fn_por_id[b["funcion_id"]]["titulo"]
                    conteo[t] = conteo.get(t, 0) + 1
            for t, n in sorted(conteo.items(), key=lambda x: -x[1])[:5]:
                L.append(f"  {t}: {n} boletos")
            if not conteo:
                L.append("  (sin ventas)")

            L += ["", "MÉTODOS DE PAGO PREFERIDOS"]
            metodos = {}
            for b in activos:
                metodos[b["metodo"]] = metodos.get(b["metodo"], 0) + 1
            total = sum(metodos.values())
            for m, n in sorted(metodos.items(), key=lambda x: -x[1]):
                L.append(f"  {m}: {n / total:.1%}")
            if not metodos:
                L.append("  (sin ventas)")
            return "\n".join(L)

    def tab_reportes(self, t):
            caja = ctk.CTkTextbox(t, font=("Consolas", 14), state="disabled")
            caja.pack(fill="both", expand=True, padx=10, pady=10)
            self.llenar_textbox(caja, self.texto_reportes())
            ctk.CTkButton(t, text="Actualizar",
                          command=lambda: self.llenar_textbox(caja, self.texto_reportes())).pack(pady=5)

    def tab_peliculas(self, t):
            ctk.CTkLabel(t, text="Alta de película", font=("Arial", 16, "bold")).pack(pady=8)
            self.pel_ent = {}
            for campo, texto in [("titulo", "Título"), ("sinopsis", "Sinopsis"),
                                 ("genero", "Género"), ("duracion", "Duración (minutos)")]:
                e = ctk.CTkEntry(t, width=420, placeholder_text=texto)
                e.pack(pady=4)
                self.pel_ent[campo] = e
            self.cb_clasif = ctk.CTkComboBox(t, values=["A", "B", "C"], state="readonly", width=420)
            self.cb_clasif.set("A")
            self.cb_clasif.pack(pady=4)

            self.poster_ruta = ""
            fila = ctk.CTkFrame(t, fg_color="transparent")
            fila.pack(pady=4)
            self.lbl_poster = ctk.CTkLabel(fila, text="Sin póster", text_color="gray", width=250)
            ctk.CTkButton(fila, text="Elegir póster", width=150,
                          command=self.elegir_poster).pack(side="left", padx=5)
            self.lbl_poster.pack(side="left", padx=5)
            ctk.CTkButton(t, text="Guardar película", command=self.guardar_pelicula).pack(pady=10)

    def elegir_poster(self):
            ruta = filedialog.askopenfilename(filetypes=[("Imágenes", "*.png *.jpg *.jpeg")])
            if ruta:
                self.poster_ruta = ruta
                self.lbl_poster.configure(text=ruta.split("/")[-1].split("\\")[-1])

    def guardar_pelicula(self):
            d = {k: e.get().strip() for k, e in self.pel_ent.items()}
            if not all(d.values()):
                messagebox.showwarning("Película", "Título, sinopsis, género y duración son obligatorios (RN-02).")
                return
            if not d["duracion"].isdigit() or int(d["duracion"]) <= 0:
                messagebox.showwarning("Película", "La duración debe ser un número de minutos mayor que 0.")
                return
            pid = max(p["id"] for p in self.peliculas_sim) + 1
            self.peliculas_sim.append({
                "id": pid, "titulo": d["titulo"], "sinopsis": d["sinopsis"],
                "clasificacion": self.cb_clasif.get(), "genero": d["genero"],
                "duracion": int(d["duracion"]), "poster": self.poster_ruta})
            self.registrar_auditoria("Alta de película", d["titulo"])
            messagebox.showinfo("Película", "Película guardada. Ya puedes programarle funciones.")
            self.recargar_admin("Películas")


    def hay_traslape(self, sala_id, inicio, duracion):
            fin = inicio + timedelta(minutes=duracion + LIMPIEZA_MIN)
            for fn in self.funciones_sim:
                if fn["sala_id"] != sala_id:
                    continue
                ini2 = datetime.strptime(f'{fn["fecha"]} {fn["hora"]}', "%Y-%m-%d %H:%M")
                fin2 = ini2 + timedelta(minutes=fn["duracion"] + LIMPIEZA_MIN)
                if inicio < fin2 and ini2 < fin:
                    return True
            return False

    def tab_funciones(self, t):
            ctk.CTkLabel(t, text="Programar función", font=("Arial", 16, "bold")).pack(pady=8)
            self.map_pel = {p["titulo"]: p["id"] for p in self.peliculas_sim}
            self.map_sala = {f'{s["nombre"]} ({s["ubicacion"]})': s["id"] for s in self.salas_sim}

            fila = ctk.CTkFrame(t, fg_color="transparent")
            fila.pack(pady=5)
            self.cb_f_pel = ctk.CTkComboBox(fila, values=list(self.map_pel), state="readonly", width=200)
            self.cb_f_pel.set(next(iter(self.map_pel)))
            self.cb_f_sala = ctk.CTkComboBox(fila, values=list(self.map_sala), state="readonly", width=220)
            self.cb_f_sala.set(next(iter(self.map_sala)))
            self.ent_f_fecha = ctk.CTkEntry(fila, width=130, placeholder_text="AAAA-MM-DD")
            self.ent_f_hora = ctk.CTkEntry(fila, width=80, placeholder_text="HH:MM")
            for w in (self.cb_f_pel, self.cb_f_sala, self.ent_f_fecha, self.ent_f_hora):
                w.pack(side="left", padx=5)
            ctk.CTkButton(t, text="Crear función", command=self.crear_funcion).pack(pady=8)

            caja = ctk.CTkTextbox(t, font=("Consolas", 13), state="disabled")
            caja.pack(fill="both", expand=True, padx=10, pady=10)
            self.llenar_textbox(caja, "\n".join(
                f'#{f["id"]} · {f["titulo"]} · {f["sala"]} · {f["fecha"]} {f["hora"]} ({f["duracion"]} min)'
                for f in sorted(self.funciones_sim, key=lambda x: (x["fecha"], x["hora"]))))

    def crear_funcion(self):
            try:
                inicio = datetime.strptime(
                    f'{self.ent_f_fecha.get().strip()} {self.ent_f_hora.get().strip()}', "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showwarning("Función", "Usa fecha AAAA-MM-DD y hora HH:MM.")
                return
            pid = self.map_pel[self.cb_f_pel.get()]
            sid = self.map_sala[self.cb_f_sala.get()]
            pel = next(p for p in self.peliculas_sim if p["id"] == pid)
            if self.hay_traslape(sid, inicio, pel["duracion"]):
                messagebox.showerror("Traslape", "La sala está ocupada en ese horario "
                                     f"(se requieren {LIMPIEZA_MIN} min de limpieza entre funciones).")
                return
            nuevo_id = max(fn["id"] for fn in self.funciones_sim) + 1
            self.funciones_sim.append(self.armar_funcion(
                nuevo_id, pid, sid, inicio.strftime("%Y-%m-%d"), inicio.strftime("%H:%M")))
            self.registrar_auditoria("Alta de función",
                                     f'{pel["titulo"]} · sala {sid} · {inicio:%Y-%m-%d %H:%M}')
            self.refrescar_cartelera()
            self.recargar_admin("Funciones")
    def hay_traslape(self, sala_id, inicio, duracion):
            fin = inicio + timedelta(minutes=duracion + LIMPIEZA_MIN)
            for fn in self.funciones_sim:
                if fn["sala_id"] != sala_id:
                    continue
                ini2 = datetime.strptime(f'{fn["fecha"]} {fn["hora"]}', "%Y-%m-%d %H:%M")
                fin2 = ini2 + timedelta(minutes=fn["duracion"] + LIMPIEZA_MIN)
                if inicio < fin2 and ini2 < fin:
                    return True
            return False

    def tab_funciones(self, t):
            ctk.CTkLabel(t, text="Programar función", font=("Arial", 16, "bold")).pack(pady=8)
            self.map_pel = {p["titulo"]: p["id"] for p in self.peliculas_sim}
            self.map_sala = {f'{s["nombre"]} ({s["ubicacion"]})': s["id"] for s in self.salas_sim}

            fila = ctk.CTkFrame(t, fg_color="transparent")
            fila.pack(pady=5)
            self.cb_f_pel = ctk.CTkComboBox(fila, values=list(self.map_pel), state="readonly", width=200)
            self.cb_f_pel.set(next(iter(self.map_pel)))
            self.cb_f_sala = ctk.CTkComboBox(fila, values=list(self.map_sala), state="readonly", width=220)
            self.cb_f_sala.set(next(iter(self.map_sala)))
            self.ent_f_fecha = ctk.CTkEntry(fila, width=130, placeholder_text="AAAA-MM-DD")
            self.ent_f_hora = ctk.CTkEntry(fila, width=80, placeholder_text="HH:MM")
            for w in (self.cb_f_pel, self.cb_f_sala, self.ent_f_fecha, self.ent_f_hora):
                w.pack(side="left", padx=5)
            ctk.CTkButton(t, text="Crear función", command=self.crear_funcion).pack(pady=8)

            caja = ctk.CTkTextbox(t, font=("Consolas", 13), state="disabled")
            caja.pack(fill="both", expand=True, padx=10, pady=10)
            self.llenar_textbox(caja, "\n".join(
                f'#{f["id"]} · {f["titulo"]} · {f["sala"]} · {f["fecha"]} {f["hora"]} ({f["duracion"]} min)'
                for f in sorted(self.funciones_sim, key=lambda x: (x["fecha"], x["hora"]))))

    def crear_funcion(self):
            try:
                inicio = datetime.strptime(
                    f'{self.ent_f_fecha.get().strip()} {self.ent_f_hora.get().strip()}', "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showwarning("Función", "Usa fecha AAAA-MM-DD y hora HH:MM.")
                return
            pid = self.map_pel[self.cb_f_pel.get()]
            sid = self.map_sala[self.cb_f_sala.get()]
            pel = next(p for p in self.peliculas_sim if p["id"] == pid)
            if self.hay_traslape(sid, inicio, pel["duracion"]):
                messagebox.showerror("Traslape", "La sala está ocupada en ese horario "
                                     f"(se requieren {LIMPIEZA_MIN} min de limpieza entre funciones).")
                return
            nuevo_id = max(fn["id"] for fn in self.funciones_sim) + 1
            self.funciones_sim.append(self.armar_funcion(
                nuevo_id, pid, sid, inicio.strftime("%Y-%m-%d"), inicio.strftime("%H:%M")))
            self.registrar_auditoria("Alta de función",
                                     f'{pel["titulo"]} · sala {sid} · {inicio:%Y-%m-%d %H:%M}')
            self.refrescar_cartelera()
            self.recargar_admin("Funciones")

    def tab_precios(self, t):
            ctk.CTkLabel(t, text="Matriz de precios", font=("Arial", 16, "bold")).pack(pady=8)
            self.lbl_precios = ctk.CTkLabel(t, justify="left", text="\n".join(
                f"{k}: ${v:.2f}" for k, v in self.tarifas_sim.items()))
            self.lbl_precios.pack(pady=5)
            fila = ctk.CTkFrame(t, fg_color="transparent")
            fila.pack(pady=10)
            self.cb_p_tipo = ctk.CTkComboBox(fila, values=list(self.tarifas_sim), state="readonly", width=180)
            self.cb_p_tipo.set(next(iter(self.tarifas_sim)))
            self.cb_p_tipo.pack(side="left", padx=5)
            self.ent_p_precio = ctk.CTkEntry(fila, width=130, placeholder_text="Nuevo precio")
            self.ent_p_precio.pack(side="left", padx=5)
            ctk.CTkButton(fila, text="Guardar", width=100,
                          command=self.guardar_precio).pack(side="left", padx=5)

    def guardar_precio(self):
            try:
                nuevo = Decimal(self.ent_p_precio.get().strip())
            except InvalidOperation:
                messagebox.showwarning("Precio", "Escribe un número, por ejemplo 13.50.")
                return
            if not nuevo.is_finite() or nuevo <= 0:
                messagebox.showwarning("Precio", "El precio debe ser mayor que 0.")
                return
            nuevo = nuevo.quantize(Decimal("0.01"))
            tipo = self.cb_p_tipo.get()
            viejo = self.tarifas_sim[tipo]
            self.tarifas_sim[tipo] = nuevo
            self.registrar_auditoria("Cambio de precio", f"{tipo}: ${viejo:.2f} → ${nuevo:.2f}")
            self.recargar_admin("Precios")

    def tab_reembolsos(self, t):
            ctk.CTkLabel(t, text="Reembolso forzado", font=("Arial", 16, "bold")).pack(pady=8)
            self.ent_r_codigo = ctk.CTkEntry(t, width=420, placeholder_text="Código de la entrada")
            self.ent_r_codigo.pack(pady=5)
            self.ent_r_motivo = ctk.CTkEntry(t, width=420, placeholder_text="Motivo (obligatorio)")
            self.ent_r_motivo.pack(pady=5)
            ctk.CTkButton(t, text="Reembolsar y liberar asiento",
                          command=self.reembolso_forzado).pack(pady=10)

    def reembolso_forzado(self):
            codigo = self.ent_r_codigo.get().strip()
            motivo = self.ent_r_motivo.get().strip()
            b = self.boletos_sim.get(codigo)
            if b is None:
                messagebox.showerror("Reembolso", "No existe una entrada con ese código.")
                return
            if b.get("reembolsado"):
                messagebox.showwarning("Reembolso", "Esa entrada ya fue reembolsada.")
                return
            if b["usado"]:
                messagebox.showwarning("Reembolso", "La entrada ya fue utilizada en la puerta.")
                return
            if not motivo:
                messagebox.showwarning("Reembolso", "Escribe el motivo; queda en la auditoría.")
                return
            b["reembolsado"] = True   # TODO: BD, anular el boleto y liberar el asiento en una transacción
            self.registrar_auditoria(
                "Reembolso forzado",
                f'{codigo[:8]}… · asiento {b["asiento"]} · ${b["precio"]:.2f} · motivo: {motivo}')
            messagebox.showinfo("Reembolso", f'Reembolso registrado: ${b["precio"]:.2f}. '
                                             "El asiento quedó libre.")
            self.ent_r_codigo.delete(0, "end")
            self.ent_r_motivo.delete(0, "end")

    def tab_auditoria(self, t):
            caja = ctk.CTkTextbox(t, font=("Consolas", 13), state="disabled")
            caja.pack(fill="both", expand=True, padx=10, pady=10)
            lineas = [f'{r["momento"]:%Y-%m-%d %H:%M:%S} · {r["usuario"]} ({r["rol"]}) · '
                      f'{r["ip"]} · {r["accion"]} · {r["detalle"]}'
                      for r in reversed(self.audit_sim)]
            self.llenar_textbox(caja, "\n".join(lineas) or "(sin operaciones registradas)")
            ctk.CTkButton(t, text="Actualizar",
                          command=lambda: self.recargar_admin("Auditoría")).pack(pady=5)

    #------------------
    def estado_boleto(self, b):
            if b.get("reembolsado"):
                return "Reembolsada"
            if b["usado"]:
                return "Utilizada"
            return "Vigente"

    def dibujar_boleto(self, parent, codigo):
            for w in parent.winfo_children():
                w.destroy()
            b = self.boletos_sim[codigo]
            fn = next((f for f in self.funciones_sim if f["id"] == b["funcion_id"]), None)
            estado = self.estado_boleto(b)

            datos = ctk.CTkFrame(parent, fg_color="transparent")
            datos.pack(side="left", padx=20, pady=20)
            ctk.CTkLabel(datos, text=fn["titulo"] if fn else "Función", font=("Arial", 18, "bold"),
                         wraplength=300, justify="left").pack(anchor="w")
            if fn:
                ctk.CTkLabel(datos, justify="left", text=(
                    f'{fn["ubicacion"]} · {fn["sala"]}\n'
                    f'{fn["fecha"]} · {fn["hora"]}')).pack(anchor="w", pady=(8, 0))
            ctk.CTkLabel(datos, justify="left", text=(
                f'Asiento: {b["asiento"]}\n'
                f'Entrada: {b.get("tipo", "")}\n'
                f'Estado: {estado}')).pack(anchor="w", pady=8)
            ctk.CTkLabel(datos, text=f"Código:\n{codigo}", text_color="gray",
                         wraplength=300, justify="left").pack(anchor="w")

            if estado == "Reembolsada":
                ctk.CTkLabel(parent, text="ENTRADA\nANULADA", font=("Arial", 22, "bold"),
                             text_color="#d93a3a", width=220, height=220).pack(
                    side="right", padx=20, pady=20)
                return
            img = self.generar_qr_pil(codigo)
            qr = ctk.CTkImage(light_image=img, dark_image=img, size=(220, 220))
            lbl = ctk.CTkLabel(parent, image=qr, text="")
            lbl.image_ref = qr   # evita que Python borre la imagen
            lbl.pack(side="right", padx=20, pady=20)

    def abrir_mis_entradas(self):
            if not self.tiene_acceso("mis_entradas"):
                messagebox.showwarning("Permisos", "No tienes permiso para esta pantalla.")
                return
            f = self.pantallas["mis_entradas"]
            for w in f.winfo_children():
                w.destroy()
            f.grid_columnconfigure(1, weight=1)
            f.grid_rowconfigure(1, weight=1)

            ctk.CTkLabel(f, text="Mis entradas", font=("Arial", 22, "bold")).grid(
                row=0, column=0, columnspan=2, pady=10)

            # RN-13: solo los boletos del usuario con sesión iniciada
            # TODO: BD, SELECT de los boletos WHERE usuario = el de la sesión
            propios = sorted(
                [(c, b) for c, b in self.boletos_sim.items()
                 if b.get("usuario") == self.usuario_actual["usuario"]],
                key=lambda x: x[1]["momento"], reverse=True)

            lista = ctk.CTkScrollableFrame(f, width=330)
            lista.grid(row=1, column=0, sticky="ns", padx=10, pady=10)
            self.detalle_mi = ctk.CTkFrame(f, corner_radius=12, border_width=1)
            self.detalle_mi.grid(row=1, column=1, sticky="n", padx=10, pady=10)
            self.mi_codigo = None

            if not propios:
                ctk.CTkLabel(lista, text="Aún no tienes entradas.").pack(pady=20)
            for codigo, b in propios:
                fn = next((x for x in self.funciones_sim if x["id"] == b["funcion_id"]), None)
                texto = (f'{fn["titulo"] if fn else "Función"}\n'
                         f'{fn["fecha"]} {fn["hora"]} · Asiento {b["asiento"]}\n'
                         f'{self.estado_boleto(b)}')
                ctk.CTkButton(lista, text=texto, anchor="w", height=60, width=300,
                              command=lambda c=codigo: self.seleccionar_mi_boleto(c)).pack(pady=4)

            fila = ctk.CTkFrame(f, fg_color="transparent")
            fila.grid(row=2, column=1, pady=5)
            ctk.CTkButton(fila, text="Guardar QR", command=self.guardar_mi_qr).pack(side="left", padx=5)
            if propios:
                self.seleccionar_mi_boleto(propios[0][0])
            self.mostrar_pantalla("mis_entradas")

    def seleccionar_mi_boleto(self, codigo):
            self.mi_codigo = codigo
            self.dibujar_boleto(self.detalle_mi, codigo)

    def guardar_mi_qr(self):
            if not self.mi_codigo:
                return
            b = self.boletos_sim[self.mi_codigo]
            if b.get("reembolsado"):
                messagebox.showinfo("Entrada", "Esta entrada fue reembolsada y ya no tiene QR.")
                return
            self.guardar_qr_codigo(self.mi_codigo, b["asiento"])

    def configurar_estilos(self):
            pass
    def actualizar_todas_las_tablas(self):
            pass


# ===== INTEGRACIÓN POSTGRESQL (sobre la interfaz existente) =====
class AppCineConBD(AppCine):
    """Flujo de venta de demostración conectado al esquema SQL proporcionado.

    El pago se simula como pide el enunciado. No es una pasarela real.
    """
    def __init__(self):
        self._asientos_reales = {}
        self._orden_pendiente = None
        self._funciones_cache = []
        self._ultimo_error_bd = False
        super().__init__()
        # El menú necesita un método de cierre de sesión que faltaba.

    def consultar(self, sql, params=None):
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    return cur.fetchall()
        except psycopg2.Error as error:
            self._ultimo_error_bd = True
            messagebox.showerror("PostgreSQL", f"No se pudo consultar la base de datos:\\n{error}")
            return None

    def cargar_funciones(self):
        filas = self.consultar("""
            SELECT f.funcion_id, p.titulo, p.sinopsis, p.clasificacion,
                   COALESCE(string_agg(DISTINCT g.nombre, ', '), 'Sin género'),
                   c.ciudad, s.nombre, f.inicio, s.sala_id, p.duracion_min,
                   c.nombre, c.direccion
            FROM funcion f
            JOIN pelicula p ON p.pelicula_id = f.pelicula_id
            JOIN sala s ON s.sala_id = f.sala_id
            JOIN cine c ON c.cine_id = s.cine_id
            LEFT JOIN pelicula_genero pg ON pg.pelicula_id = p.pelicula_id
            LEFT JOIN genero g ON g.genero_id = pg.genero_id
            WHERE f.activa = TRUE AND p.activa = TRUE AND f.inicio > NOW()
            GROUP BY f.funcion_id, p.pelicula_id, c.cine_id, s.sala_id
            ORDER BY f.inicio, p.titulo
        """)
        resultado = []
        if filas is None:
            return resultado
        for fid, titulo, sinopsis, clasif, genero, ciudad, sala, inicio, sid, dur, cine, direccion in filas:
            resultado.append(dict(id=fid, titulo=titulo, sinopsis=sinopsis,
                clasificacion=clasif, genero=genero, ubicacion=ciudad,
                sala=sala, fecha=inicio.strftime('%Y-%m-%d'),
                hora=inicio.strftime('%H:%M'), sala_id=sid, duracion=dur,
                cine=cine, direccion=direccion, filas=0, cols=0))
        self._funciones_cache = resultado
        return resultado

    def refrescar_cartelera(self):
        for w in self.lista.winfo_children():
            w.destroy()
        funciones = self.cargar_funciones()
        ubicaciones = ['Todas'] + sorted({f['ubicacion'] for f in funciones})
        generos = ['Todos'] + sorted({g.strip() for f in funciones
                                      for g in f['genero'].split(',')})
        self.cb_ubicacion.configure(values=ubicaciones)
        self.cb_genero.configure(values=generos)
        if self.cb_ubicacion.get() not in ubicaciones:
            self.cb_ubicacion.set('Todas')
        if self.cb_genero.get() not in generos:
            self.cb_genero.set('Todos')
        ub, gen, fecha = self.cb_ubicacion.get(), self.cb_genero.get(), self.ent_fecha.get().strip()
        filtradas = [f for f in funciones if
            (ub == 'Todas' or f['ubicacion'] == ub) and
            (gen == 'Todos' or gen in [x.strip() for x in f['genero'].split(',')]) and
            (not fecha or f['fecha'].startswith(fecha))]
        if not filtradas:
            ctk.CTkLabel(self.lista, text='No hay funciones futuras con esos filtros en PostgreSQL.').pack(pady=20)
        for i, fn in enumerate(filtradas):
            tarjeta = ctk.CTkFrame(self.lista, corner_radius=10, border_width=1)
            tarjeta.grid(row=i // COLUMNAS_CARTELERA, column=i % COLUMNAS_CARTELERA,
                         padx=10, pady=10, sticky='nsew')
            for texto in (fn['titulo'], f"Clasificación {fn['clasificacion']} · {fn['genero']}",
                          fn['sinopsis'], f"{fn['cine']} · {fn['ubicacion']}\\n{fn['direccion']}\\n{fn['sala']} · {fn['fecha']} {fn['hora']}"):
                ctk.CTkLabel(tarjeta, text=texto, wraplength=240, justify='left').pack(padx=12,pady=5)
            ctk.CTkButton(tarjeta, text='Elegir', command=lambda x=fn: self.elegir_funcion(x)).pack(padx=12,pady=10)

    def cargar_estados_asientos(self, funcion_id):
        filas = self.consultar("""
            SELECT a.asiento_id, a.fila, a.numero,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM boleto b WHERE b.funcion_id = %s
                       AND b.asiento_id = a.asiento_id AND b.estado <> 'ANULADO'
                   ) THEN 'ocupado'
                   WHEN EXISTS (
                       SELECT 1 FROM bloqueo_asiento bl WHERE bl.funcion_id = %s
                       AND bl.asiento_id = a.asiento_id AND bl.expira_en > NOW()
                   ) THEN 'bloqueado' ELSE 'disponible' END
            FROM asiento a JOIN funcion f ON f.sala_id = a.sala_id
            WHERE f.funcion_id = %s ORDER BY a.fila, a.numero
        """, (funcion_id, funcion_id, funcion_id))
        self._asientos_reales = {}
        estados = {}
        if filas:
            for aid, fila, numero, estado in filas:
                codigo = f'{fila}{numero}'
                self._asientos_reales[codigo] = aid
                estados[codigo] = estado
        return estados

    def construir_mapa_asientos(self):
        marco = self.pantallas['asientos']
        for w in marco.winfo_children(): w.destroy()
        fn = self.funcion_elegida
        ctk.CTkLabel(marco, text=f"{fn['titulo']} · {fn['sala']} · {fn['hora']}",
                     font=('Arial',20,'bold')).pack(pady=10)
        estados = self.cargar_estados_asientos(fn['id'])
        malla = ctk.CTkScrollableFrame(marco, width=900, height=400)
        malla.pack(fill='both', expand=True, padx=10,pady=5)
        self.botones_asientos = {}
        filas = sorted({''.join(c for c in codigo if not c.isdigit()) for codigo in estados})
        for codigo, estado in estados.items():
            fila = ''.join(c for c in codigo if not c.isdigit())
            numero = int(codigo[len(fila):])
            b = ctk.CTkButton(malla, text=codigo, width=49, height=32,
                 fg_color=COLORES[estado], hover=False,
                 command=lambda x=codigo: self.click_asiento(x))
            b.grid(row=filas.index(fila),column=numero-1,padx=2,pady=2)
            if estado != 'disponible': b.configure(state='disabled')
            self.botones_asientos[codigo] = b
        if not estados:
            ctk.CTkLabel(malla, text='Esta sala no tiene asientos registrados en PostgreSQL.').pack()
        self.lbl_resumen = ctk.CTkLabel(marco,text='Asientos: ninguno')
        self.lbl_resumen.pack(pady=5)
        botones = ctk.CTkFrame(marco)
        botones.pack(pady=6)
        ctk.CTkButton(botones,text='Volver',command=lambda:self.mostrar_pantalla('cartelera')).pack(side='left',padx=5)
        ctk.CTkButton(botones,text='Continuar',command=self.continuar_a_tarifas).pack(side='left',padx=5)

    def continuar_a_tarifas(self):
        if not self.asientos_elegidos:
            messagebox.showwarning('Asientos','Selecciona al menos un asiento.')
            return
        if not self.usuario_actual:
            self.accion_pendiente = 'compra'
            messagebox.showinfo('Cuenta','Inicia sesión para comprar.')
            self.abrir_login()
            return
        if self.rol_actual() not in ROLES_COMPRADORES:
            messagebox.showwarning('Permisos','Este rol no puede comprar.')
            return
        # Reservamos en una transacción; los bloqueos de otras órdenes se respetan.
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cur:
                    cur.execute('DELETE FROM bloqueo_asiento WHERE expira_en <= NOW()')
                    cur.execute('SELECT 1 FROM funcion WHERE funcion_id=%s AND activa AND inicio>NOW()', (self.funcion_elegida['id'],))
                    if not cur.fetchone(): raise ValueError('La función ya no está disponible.')
                    cur.execute('''INSERT INTO orden (usuario_id,estado,subtotal,descuento,cargo_servicio,total)
                                   VALUES (%s,'PENDIENTE',0,0,0,0) RETURNING orden_id''',
                                (self.usuario_actual['usuario_id'],))
                    oid = cur.fetchone()[0]
                    for codigo in sorted(self.asientos_elegidos):
                        aid = self._asientos_reales[codigo]
                        cur.execute('SELECT 1 FROM boleto WHERE funcion_id=%s AND asiento_id=%s AND estado<>\'ANULADO\'',
                                    (self.funcion_elegida['id'], aid))
                        if cur.fetchone(): raise ValueError(f'El asiento {codigo} ya está vendido.')
                        cur.execute('''INSERT INTO bloqueo_asiento(orden_id,funcion_id,asiento_id,expira_en)
                                       VALUES (%s,%s,%s,NOW()+INTERVAL '2 minutes')''',
                                    (oid,self.funcion_elegida['id'],aid))
            self._orden_pendiente = oid
        except (psycopg2.Error, ValueError, KeyError) as error:
            messagebox.showerror('Reserva',f'No se pudo reservar: {error}')
            self.asientos_elegidos.clear()
            self.construir_mapa_asientos()
            return
        self.iniciar_bloqueo()
        if self.construir_tarifas():
            self.mostrar_pantalla('tarifas')

    def cargar_tarifas(self, funcion_id):
        filas = self.consultar('''SELECT t.nombre, MIN(a.precio)
                FROM tarifa a JOIN tipo_entrada t ON t.tipo_entrada_id=a.tipo_entrada_id
                JOIN funcion f ON f.funcion_id=%s
                WHERE a.dia_semana=(EXTRACT(DOW FROM f.inicio)::int)
                GROUP BY t.nombre ORDER BY t.nombre''', (funcion_id,))
        # Este formulario tiene un solo precio por categoría; impedimos cobrar
        # incorrectamente cuando los asientos elegidos pertenecen a zonas distintas.
        ids = [self._asientos_reales[c] for c in self.asientos_elegidos]
        if ids:
            diferencias = self.consultar('''SELECT te.nombre, COUNT(DISTINCT t.precio)
                FROM asiento a JOIN tarifa t ON t.zona_id=a.zona_id
                JOIN tipo_entrada te ON te.tipo_entrada_id=t.tipo_entrada_id
                JOIN funcion f ON f.funcion_id=%s
                WHERE a.asiento_id=ANY(%s) AND t.dia_semana=EXTRACT(DOW FROM f.inicio)::int
                GROUP BY te.nombre HAVING COUNT(DISTINCT t.precio)>1''', (funcion_id,ids))
            if diferencias is None or diferencias:
                messagebox.showerror('Tarifas', 'Hay precios diferentes según zona o no se pudo comprobarlos. '
                   'Esta versión requiere precios iguales entre las zonas elegidas.')
                return {}
        return {nombre: Decimal(precio) for nombre,precio in (filas or [])}

    def construir_tarifas(self):
        precios = self.cargar_tarifas(self.funcion_elegida['id'])
        if not precios:
            messagebox.showerror('Tarifas','No hay tarifas cargadas para el día de la función.')
            self.liberar_asientos()
            self.elegir_funcion(self.funcion_elegida)
            return False
        self.tarifas = precios
        super().construir_tarifas()
        return True

    def liberar_asientos(self):
        self.cancelar_bloqueo()
        if self._orden_pendiente is not None:
            try:
                with psycopg2.connect(**self.conn_params) as conn:
                    with conn.cursor() as cur:
                        cur.execute('DELETE FROM bloqueo_asiento WHERE orden_id=%s',(self._orden_pendiente,))
                        cur.execute("UPDATE orden SET estado='CANCELADA' WHERE orden_id=%s AND estado='PENDIENTE'",(self._orden_pendiente,))
            except psycopg2.Error as error:
                messagebox.showerror('PostgreSQL',str(error))
            self._orden_pendiente = None
        self.asientos_elegidos = set()
        self.compra_actual = None

    def pago_aprobado(self, metodo, ultimos4):
        if self._orden_pendiente is None:
            messagebox.showerror('Pago','No existe una reserva activa.')
            return
        c = self.compra_actual
        codigos = {asiento: str(uuid.uuid4()) for asiento in c['asientos']}
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cur:
                    cur.execute('''SELECT asiento_id FROM bloqueo_asiento
                        WHERE orden_id=%s AND funcion_id=%s AND expira_en>NOW() FOR UPDATE''',
                        (self._orden_pendiente,c['funcion']['id']))
                    bloqueados = {r[0] for r in cur.fetchall()}
                    if bloqueados != {self._asientos_reales[k] for k in c['asientos']}:
                        raise ValueError('La reserva venció o algunos asientos dejaron de estar bloqueados.')
                    cur.execute('SELECT metodo_pago_id FROM metodo_pago WHERE nombre=%s',(metodo,))
                    metodo_fila = cur.fetchone()
                    if not metodo_fila:
                        cur.execute('INSERT INTO metodo_pago(nombre) VALUES(%s) RETURNING metodo_pago_id',(metodo,))
                        metodo_id = cur.fetchone()[0]
                    else: metodo_id = metodo_fila[0]
                    cur.execute('''UPDATE orden SET estado='PAGADA', subtotal=%s, descuento=%s,
                               cargo_servicio=%s,total=%s WHERE orden_id=%s AND estado='PENDIENTE' ''',
                        (c['subtotal'],c['descuento'],c['cargo'],c['total'],self._orden_pendiente))
                    if cur.rowcount != 1: raise ValueError('La orden no está pendiente.')
                    cur.execute('''INSERT INTO pago(orden_id,metodo_pago_id,monto,estado,ultimos4)
                                   VALUES(%s,%s,%s,'APROBADO',%s)''',
                                (self._orden_pendiente,metodo_id,c['total'],ultimos4))
                    for asiento,codigo in codigos.items():
                        tipo = c['asientos'][asiento]
                        cur.execute('SELECT tipo_entrada_id FROM tipo_entrada WHERE nombre=%s',(tipo,))
                        fila=cur.fetchone()
                        if not fila: raise ValueError(f'No existe el tipo de entrada {tipo}.')
                        cur.execute('''INSERT INTO boleto(orden_id,funcion_id,asiento_id,tipo_entrada_id,precio,codigo_qr)
                            VALUES(%s,%s,%s,%s,%s,%s)''',
                            (self._orden_pendiente,c['funcion']['id'],self._asientos_reales[asiento],fila[0],self.tarifas[tipo],codigo))
                    cur.execute('DELETE FROM bloqueo_asiento WHERE orden_id=%s',(self._orden_pendiente,))
        except (psycopg2.Error,ValueError) as error:
            messagebox.showerror('Pago',f'No se confirmó la compra en PostgreSQL: {error}')
            return
        self.cancelar_bloqueo()
        self._orden_pendiente = None
        c['metodo'],c['ultimos4'],c['boletos'] = metodo,ultimos4,codigos
        self.construir_confirmacion()
        self.mostrar_pantalla('confirmacion')

    def pago_rechazado(self):
        self.liberar_asientos()
        messagebox.showwarning('Pago rechazado','Pago simulado rechazado. Se liberaron los asientos.')
        self.refrescar_cartelera()
        self.mostrar_pantalla('cartelera')

    def dibujar_boleto(self,parent,codigo):
        for w in parent.winfo_children():w.destroy()
        filas=self.consultar('''SELECT p.titulo,c.ciudad,s.nombre,f.inicio,a.fila,a.numero,
                            t.nombre,b.estado FROM boleto b
                            JOIN funcion f ON b.funcion_id=f.funcion_id
                            JOIN pelicula p ON f.pelicula_id=p.pelicula_id
                            JOIN sala s ON f.sala_id=s.sala_id JOIN cine c ON c.cine_id=s.cine_id
                            JOIN asiento a ON a.asiento_id=b.asiento_id
                            JOIN tipo_entrada t ON t.tipo_entrada_id=b.tipo_entrada_id
                            WHERE b.codigo_qr=%s''',(codigo,))
        if not filas:
            ctk.CTkLabel(parent,text='Boleto no encontrado en PostgreSQL').pack()
            return
        titulo,ciudad,sala,inicio,fila,numero,tipo,estado=filas[0]
        text=f'{titulo}\\n{ciudad} · {sala}\\n{inicio:%Y-%m-%d %H:%M}\\nAsiento: {fila}{numero} · {tipo}\\nEstado: {estado}\\nCódigo: {codigo}'
        ctk.CTkLabel(parent,text=text,justify='left',wraplength=350).pack(side='left',padx=20,pady=20)
        if estado=='ANULADO': return
        imagen=self.generar_qr_pil(codigo)
        qr=ctk.CTkImage(light_image=imagen,dark_image=imagen,size=(200,200))
        lbl=ctk.CTkLabel(parent,image=qr,text='')
        lbl.image_ref=qr
        lbl.pack(side='right',padx=20,pady=20)

    def abrir_mis_entradas(self):
        if not self.usuario_actual:return
        f=self.pantallas['mis_entradas']
        for w in f.winfo_children():w.destroy()
        ctk.CTkLabel(f,text='Mis entradas (PostgreSQL)',font=('Arial',22,'bold')).pack(pady=10)
        filas=self.consultar('''SELECT b.codigo_qr,p.titulo,f.inicio,a.fila,a.numero,b.estado
                FROM boleto b JOIN orden o ON o.orden_id=b.orden_id
                JOIN funcion f ON f.funcion_id=b.funcion_id
                JOIN pelicula p ON p.pelicula_id=f.pelicula_id
                JOIN asiento a ON a.asiento_id=b.asiento_id
                WHERE o.usuario_id=%s ORDER BY o.creada_en DESC''',
                (self.usuario_actual['usuario_id'],)) or []
        self.detalle_mi=ctk.CTkFrame(f)
        self.detalle_mi.pack(side='right',padx=10,pady=10)
        lista=ctk.CTkScrollableFrame(f,width=370)
        lista.pack(side='left',fill='y',padx=10,pady=10)
        self.mi_codigo=None
        for codigo,titulo,inicio,fila,numero,estado in filas:
            ctk.CTkButton(lista,text=f'{titulo} · {inicio:%Y-%m-%d %H:%M}\\n{fila}{numero} · {estado}',
                command=lambda c=codigo:self.seleccionar_mi_boleto(c)).pack(pady=5)
        ctk.CTkButton(lista,text='Guardar QR seleccionado',command=self.guardar_mi_qr).pack(pady=10)
        if filas:self.seleccionar_mi_boleto(filas[0][0])
        self.mostrar_pantalla('mis_entradas')

    def guardar_mi_qr(self):
        if not self.mi_codigo:return
        ruta=filedialog.asksaveasfilename(defaultextension='.png',filetypes=[('PNG','*.png')])
        if ruta:self.generar_qr_pil(self.mi_codigo).save(ruta)

    def evaluar_entrada(self,codigo,fn_puerta,ahora):
        # El UPDATE condicional permite utilizar el boleto una sola vez.
        try:
            with psycopg2.connect(**self.conn_params) as conn:
                with conn.cursor() as cur:
                    cur.execute('''SELECT b.boleto_id,b.funcion_id,b.estado,a.fila,a.numero,f.inicio
                        FROM boleto b JOIN asiento a ON a.asiento_id=b.asiento_id
                        JOIN funcion f ON f.funcion_id=b.funcion_id
                        WHERE b.codigo_qr=%s FOR UPDATE OF b''',(codigo,))
                    fila=cur.fetchone()
                    if not fila:return False,'Código no válido'
                    bid,fid,estado,letra,numero,inicio=fila
                    if estado=='USADO':return False,'Entrada ya utilizada'
                    if estado=='ANULADO':return False,'Entrada anulada'
                    if fid!=fn_puerta['id']:return False,'Entrada de otra función'
                    if not(inicio-timedelta(minutes=MIN_ANTES)<=ahora<=inicio+timedelta(minutes=MIN_DESPUES)):
                        return False,'Fuera del horario de acceso'
                    cur.execute("UPDATE boleto SET estado='USADO',usado_en=NOW() WHERE boleto_id=%s AND estado='EMITIDO'",(bid,))
                    if cur.rowcount != 1:return False,'Entrada no disponible'
                    return True,f'Acceso permitido · Asiento {letra}{numero}'
        except psycopg2.Error as error:
            messagebox.showerror('Check-in',str(error))
            return False,'Error de conexión'

    def construir_checkin(self):
        if not self.cargar_funciones():
            messagebox.showwarning('Check-in','No hay funciones futuras disponibles para seleccionar.')
            return
        super().construir_checkin()

    def registrar_auditoria(self,accion,detalle):
        # Los scripts aportados aún no contienen admin_operacion_audit.
        self.audit_sim.append({'momento':datetime.now(),
            'usuario':self.usuario_actual['usuario'] if self.usuario_actual else 'sin sesión',
            'rol':self.rol_actual(), 'ip':'127.0.0.1','accion':accion,'detalle':detalle})

    def abrir_admin(self):
        # No presentar formularios simulados como si actualizaran PostgreSQL.
        messagebox.showinfo('Administración pendiente',
          'Este módulo aún requiere integración SQL y tablas de auditoría.\\n'
          'La cartelera, compras y boletos son los componentes conectados en esta versión.')

    def cerrar_sesion(self):
        if self._orden_pendiente is not None:self.liberar_asientos()
        self.usuario_actual=None
        self.actualizar_menu()
        self.refrescar_cartelera()
        self.mostrar_pantalla('cartelera')

if __name__ == "__main__":
       app = AppCineConBD()
       app.mainloop()






        




























    