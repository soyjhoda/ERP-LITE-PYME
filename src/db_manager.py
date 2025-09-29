import sqlite3
from sqlite3 import Error
import os

DB_FILE = 'profitus.db'

class DatabaseManager:
    """Clase para manejar la conexión y las operaciones de la base de datos SQLite."""
    
    def __init__(self):
        """Inicializa la conexión con la base de datos y crea tablas si no existen."""
        self.conn = None
        self.connect()
        self.create_default_tables()
        self.initialize_default_config() # <-- Nueva inicialización

    def connect(self):
        """Establece la conexión con la base de datos."""
        try:
            # Asegurarse de que la conexión use el modo de fila (diccionario) para futuras consultas
            self.conn = sqlite3.connect(DB_FILE)
            self.conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
            print(f"Conectado a la DB: {DB_FILE}")
        except Error as e:
            print(f"Error al conectar con SQLite: {e}")
            
    def close(self):
        """Cierra la conexión con la base de datos."""
        if self.conn:
            self.conn.close()
            print("Conexión a la DB cerrada.")

    def execute_query(self, query, params=()):
        """Ejecuta consultas de modificación (INSERT, UPDATE, DELETE)."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor
        except Error as e:
            print(f"Error al ejecutar consulta: {e}")
            return None

    def fetch_one(self, query, params=()):
        """Ejecuta consultas de selección y devuelve una sola fila."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Error as e:
            print(f"Error al obtener una fila: {e}")
            return None

    def fetch_all(self, query, params=()):
        """Ejecuta consultas de selección y devuelve todas las filas."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener todas las filas: {e}")
            return []

    def create_default_tables(self):
        """Crea las tablas de usuarios, productos y configuración si no existen."""
        
        # 1. Tabla de Usuarios
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'empleado'
            )
        """)
        
        # 2. Tabla de Productos (Esencial para Inventario)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL UNIQUE,
                nombre TEXT NOT NULL,
                stock REAL NOT NULL DEFAULT 0,
                precio_venta REAL NOT NULL,
                precio_costo REAL NOT NULL,
                categoria TEXT
            )
        """)

        # 3. Nueva Tabla de Configuración (para parámetros globales como la Tasa de Cambio)
        # Usamos una estructura simple clave-valor, ideal para SQLite
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS configuracion (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
    def initialize_default_config(self):
        """Inserta la configuración inicial por defecto (ej. Tasa de Cambio)."""
        # Insertar usuario administrador por defecto si no existe
        if not self.fetch_one("SELECT id FROM usuarios WHERE username = 'admin'"):
            self.execute_query("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                               ("admin", "1234", "admin"))
            print("Usuario 'admin' creado.")
            
        # Insertar productos de prueba si no hay ninguno
        if not self.fetch_one("SELECT id FROM productos"):
            products_to_insert = [
                ('P001', 'Laptop Gamer X', 10, 850.50, 600.00, 'Electrónica'),
                ('P002', 'Monitor Curvo 27"', 25, 250.00, 180.00, 'Electrónica'),
                ('P003', 'Mouse Inalámbrico', 50, 15.75, 8.50, 'Accesorios'),
            ]
            for prod in products_to_insert:
                self.execute_query("INSERT INTO productos (codigo, nombre, stock, precio_venta, precio_costo, categoria) VALUES (?, ?, ?, ?, ?, ?)", prod)
            print("Productos de prueba insertados.")
            
        # Insertar Tasa de Cambio por defecto (si no existe)
        if not self.fetch_one("SELECT key FROM configuracion WHERE key = 'exchange_rate'"):
            self.execute_query("INSERT INTO configuracion (key, value) VALUES (?, ?)", 
                               ("exchange_rate", "36.00")) # Valor por defecto
            print("Tasa de cambio por defecto (36.00) inicializada.")

    # --- Funciones Específicas para Tasa de Cambio ---

    def get_exchange_rate(self):
        """Obtiene la tasa de cambio actual desde la tabla de configuración."""
        row = self.fetch_one("SELECT value FROM configuracion WHERE key = 'exchange_rate'")
        if row:
            try:
                # El valor está guardado como TEXTO, lo convertimos a FLOAT
                return float(row['value']) 
            except ValueError:
                print("Advertencia: El valor de la tasa de cambio no es un número válido.")
                return None
        return None

    def set_exchange_rate(self, rate):
        """Guarda o actualiza la tasa de cambio en la tabla de configuración."""
        # SQLite usa INSERT OR REPLACE para asegurarse de que siempre haya solo una entrada para 'exchange_rate'
        self.execute_query("""
            INSERT OR REPLACE INTO configuracion (key, value)
            VALUES ('exchange_rate', ?)
        """, (str(rate),))
