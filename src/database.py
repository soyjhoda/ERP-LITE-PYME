import sqlite3
from decimal import Decimal, getcontext

# Configura la precisión global de decimal a 28 dígitos (estándar para alta precisión)
getcontext().prec = 28

class DatabaseManager:
    def __init__(self, db_name="profitus.db"):
        self.db_name = db_name
        self._initialize_db()

    def _initialize_db(self):
        """Inicializa la base de datos y crea las tablas si no existen."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Tabla de Usuarios
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY,
                    usuario TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    rol TEXT NOT NULL DEFAULT 'empleado'
                )
            """)

            # Tabla de Productos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY,
                    codigo TEXT UNIQUE,
                    nombre TEXT NOT NULL,
                    stock INTEGER NOT NULL DEFAULT 0,
                    precio_venta REAL NOT NULL DEFAULT 0.00,
                    precio_costo REAL NOT NULL DEFAULT 0.00,
                    categoria TEXT
                )
            """)
            
            # Insertar usuario administrador si no existe
            cursor.execute("SELECT id FROM usuarios WHERE usuario='admin'")
            if cursor.fetchone() is None:
                # La contraseña se guarda en texto plano solo por simplicidad de este proyecto.
                # En un entorno real, DEBE usarse hashing (ej. bcrypt).
                cursor.execute("INSERT INTO usuarios (usuario, password, rol) VALUES (?, ?, ?)", 
                               ('admin', '1234', 'administrador'))
                
            # Insertar productos de prueba si no existen
            cursor.execute("SELECT id FROM productos LIMIT 1")
            if cursor.fetchone() is None:
                products_to_insert = [
                    ('LPT001', 'Laptop Gamer X', 10, 850.50, 700.00, 'Electrónica'),
                    ('MON002', 'Monitor Curvo 27"', 5, 250.75, 200.00, 'Periféricos'),
                    ('MOU003', 'Mouse Inalámbrico RGB', 50, 15.99, 10.00, 'Periféricos'),
                ]
                cursor.executemany("INSERT INTO productos (codigo, nombre, stock, precio_venta, precio_costo, categoria) VALUES (?, ?, ?, ?, ?, ?)", products_to_insert)

            conn.commit()
            print(f"Conectado a la DB: {self.db_name}")

        except sqlite3.Error as e:
            print(f"Error al inicializar la base de datos: {e}")
        finally:
            if conn:
                conn.close()

    def _get_connection(self):
        """Abre y devuelve una conexión a la base de datos."""
        conn = sqlite3.connect(self.db_name)
        return conn
    
    def execute_query(self, query, params=()):
        """Ejecuta una consulta (INSERT, UPDATE, DELETE)."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def fetch_all(self, query, params=()):
        """
        Ejecuta una consulta SELECT y devuelve todos los resultados.
        Convierte los valores 'float' (que vienen de los campos REAL de SQLite) a Decimal
        para garantizar la precisión monetaria.
        """
        conn = None
        results = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            for row in cursor.fetchall():
                new_row = list(row)
                for idx, item in enumerate(new_row):
                    # Si el ítem es un float, lo convertimos a Decimal.
                    # Esto garantiza que todos los precios se lean con precisión.
                    if isinstance(item, float):
                        try:
                            # Convertimos el float a cadena antes de Decimal para evitar la pérdida de precisión
                            new_row[idx] = Decimal(str(item)).quantize(Decimal("0.01")) 
                        except Exception:
                            new_row[idx] = Decimal('0.00')
                results.append(tuple(new_row))
            return results
        except sqlite3.Error as e:
            print(f"Error al obtener todos los resultados: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def fetch_one(self, query, params=()):
        """Ejecuta una consulta SELECT y devuelve el primer resultado."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                new_row = list(row)
                for idx, item in enumerate(new_row):
                    if isinstance(item, float):
                        try:
                            new_row[idx] = Decimal(str(item)).quantize(Decimal("0.01"))
                        except Exception:
                            new_row[idx] = Decimal('0.00')
                return tuple(new_row)
            return row
        except sqlite3.Error as e:
            print(f"Error al obtener un resultado: {e}")
            return None
        finally:
            if conn:
                conn.close()
                
    def check_user(self, username, password):
        """Verifica las credenciales del usuario."""
        query = "SELECT id, rol FROM usuarios WHERE usuario = ? AND password = ?"
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, (username, password))
            return cursor.fetchone()
        except sqlite3.Error as e:
            print(f"Error al verificar el usuario: {e}")
            return None
        finally:
            if conn:
                conn.close()