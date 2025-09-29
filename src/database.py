import sqlite3
from datetime import datetime, timedelta

class DatabaseManager:
    """Clase para gestionar la conexión y operaciones con la base de datos SQLite."""

    def __init__(self, db_path='profitus.db'):
        super().__init__()
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables() 
        self._insert_initial_data()

    def connect(self):
        """Establece la conexión con la base de datos."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            self.cursor.execute("PRAGMA foreign_keys = ON")
        except sqlite3.Error as e:
            print(f"Error al conectar a la base de datos: {e}")

    def close(self):
        """Cierra la conexión con la base de datos."""
        if self.conn:
            self.conn.close()

    def commit(self):
        """Aplica los cambios pendientes a la base de datos."""
        if self.conn:
            self.conn.commit()

    def rollback(self):
        """Deshace los cambios pendientes (útil para transacciones fallidas)."""
        if self.conn:
            self.conn.rollback()

    def execute_query(self, query, params=()):
        """Ejecuta una consulta de escritura (INSERT, UPDATE, DELETE)."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.rowcount 
        except sqlite3.Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return None

    def execute_query_with_last_id(self, query, params=()):
        """Ejecuta un INSERT y retorna el ID de la última fila insertada."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al ejecutar INSERT y obtener ID: {e}")
            return None

    def fetch_one(self, query, params=()):
        """Ejecuta una consulta de lectura y retorna un solo resultado."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al leer la consulta: {e}")
            return None

    def fetch_all(self, query, params=()):
        """Ejecuta una consulta de lectura y retorna todos los resultados."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error al leer la consulta: {e}")
            return []

    def create_tables(self):
        """Crea las tablas necesarias si no existen con la estructura final."""
        try:
            # 1. Tabla de Usuarios
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    rol TEXT NOT NULL 
                )
            """)

            # 2. Tabla de Configuración (Tasa, Licencia, Nombre de Negocio)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    clave TEXT PRIMARY KEY,
                    valor TEXT
                )
            """)

            # 3. Tabla de Proveedores 
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS proveedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT,
                    email TEXT
                )
            """)
            
            # 4. Tabla de Inventario (¡Estructura Final CORREGIDA!)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_cliente TEXT UNIQUE,         -- Nombre de columna correcto (buscado por PDV)
                    producto TEXT NOT NULL,
                    unidad_medida TEXT,             
                    marca TEXT,                     
                    categoria TEXT,                 
                    proveedor_id INTEGER,           
                    stock INTEGER NOT NULL,
                    stock_minimo INTEGER DEFAULT 5, 
                    precio_costo_usd REAL NOT NULL,
                    precio_venta_usd REAL NOT NULL,
                    FOREIGN KEY(proveedor_id) REFERENCES proveedores(id)
                )
            """)
            
            # 5. Tabla de Ventas (Encabezado)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS ventas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha_hora TEXT NOT NULL,
                    total_usd REAL NOT NULL,
                    tasa_bcv REAL NOT NULL,
                    total_bs REAL NOT NULL,
                    metodo_pago TEXT,
                    usuario_id INTEGER,
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                )
            """)

            # 6. Tabla de Detalle de Venta
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS detalle_venta (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    venta_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    nombre_producto TEXT NOT NULL,
                    cantidad INTEGER NOT NULL,
                    precio_unitario_usd REAL NOT NULL,
                    subtotal_usd REAL NOT NULL,
                    FOREIGN KEY(venta_id) REFERENCES ventas(id),
                    FOREIGN KEY(producto_id) REFERENCES inventario(id)
                )
            """)
            
            self.conn.commit()
            print("Tablas verificadas/creadas exitosamente.")

        except Exception as e:
            print(f"Error al crear tablas: {e}")

    def _insert_initial_data(self):
        """Inserta el usuario Administrador y la configuración inicial."""
        
        # 1. Insertar el usuario administrador (Si no existe)
        try:
            self.cursor.execute("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                                ('admin', '1234', 'administrador'))
            self.conn.commit()
            print("Usuario 'admin' (pass: 1234) creado.")
        except sqlite3.IntegrityError:
            pass
            
        # 2. Insertar Nombre del Negocio Inicial
        try:
            self.cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)", 
                                ('nombre_negocio', 'PROFITUS - Negocio Ejemplo')) 
            self.conn.commit()
        except Exception:
            pass

        # 3. Insertar Tasa de Cambio Inicial
        try:
            self.cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)", 
                                ('tasa_cambio', '36.00')) 
            self.conn.commit()
        except Exception:
            pass 

        # 4. Insertar la Fecha de Expiración de Soporte
        try:
            fecha_expiracion = (datetime.now() + timedelta(days=120)).strftime('%Y-%m-%d')
            self.cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)", 
                                ('fecha_licencia', fecha_expiracion)) 
            self.conn.commit()
        except Exception:
            pass 

        # 5. Insertar un proveedor por defecto 
        try:
            self.cursor.execute("INSERT OR IGNORE INTO proveedores (id, nombre, telefono) VALUES (?, ?, ?)", 
                                (1, "(Sin Proveedor)", "N/A")) 
            self.conn.commit()
        except Exception:
            pass