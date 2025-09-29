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

    def connect(self):
        """Establece la conexión con la base de datos."""
        try:
            self.conn = sqlite3.connect(DB_FILE)
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
        """Crea las tablas de usuarios y productos si no existen."""
        # Tabla de Usuarios
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'empleado'
            )
        """)
        
        # Tabla de Productos (Esencial para Inventario)
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
        
        # Insertar usuario administrador por defecto si no existe
        if not self.fetch_one("SELECT id FROM usuarios WHERE username = 'admin'"):
            self.execute_query("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                               ("admin", "1234", "admin"))
            print("Usuario 'admin' creado.")
            
        # Insertar algunos productos de prueba si no hay ninguno
        if not self.fetch_one("SELECT id FROM productos"):
            products_to_insert = [
                ('P001', 'Laptop Gamer X', 10, 850.50, 600.00, 'Electrónica'),
                ('P002', 'Monitor Curvo 27"', 25, 250.00, 180.00, 'Electrónica'),
                ('P003', 'Mouse Inalámbrico', 50, 15.75, 8.50, 'Accesorios'),
            ]
            for prod in products_to_insert:
                self.execute_query("INSERT INTO productos (codigo, nombre, stock, precio_venta, precio_costo, categoria) VALUES (?, ?, ?, ?, ?, ?)", prod)
            print("Productos de prueba insertados.")