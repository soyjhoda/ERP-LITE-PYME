import sqlite3
from decimal import Decimal, getcontext

# Configura la precisión global de decimal a 28 dígitos (estándar para alta precisión)
getcontext().prec = 28

class DatabaseManager:
    def __init__(self, db_name="profitus.db"):
        self.db_name = db_name
        self._initialize_db()

    def _initialize_db(self):
        """Inicializa la base de datos y crea las tablas y realiza migraciones si no existen."""
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # --- TABLA DE USUARIOS (Sin cambios) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY,
                    usuario TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    rol TEXT NOT NULL DEFAULT 'empleado'
                )
            """)
            
            # --- NUEVA TABLA DE CONFIGURACIÓN GLOBAL (PARA TASA DE CAMBIO) ---
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS configuracion (
                    clave TEXT PRIMARY KEY,
                    valor REAL
                )
            """)

            # Insertar la tasa de cambio inicial si no existe. 
            # Usaremos 36.50 como valor inicial Bs/USD.
            cursor.execute("INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)", 
                           ('tasa_usd_bs', 36.50))
            
            # --- TABLA DE PRODUCTOS BASE ---
            # Creamos la tabla si es la primera vez que se inicia la DB
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
            
            # --- MIGRACIONES: Agregar nuevas columnas si no existen ---
            
            # Columna: Stock Mínimo (Valor por defecto 5)
            try:
                cursor.execute("ALTER TABLE productos ADD COLUMN stock_minimo INTEGER DEFAULT 5")
            except sqlite3.OperationalError:
                pass # La columna ya existe, no hacemos nada
                
            # Columna: Porcentaje de Margen (Valor por defecto 30.00%)
            try:
                cursor.execute("ALTER TABLE productos ADD COLUMN porc_margen REAL DEFAULT 30.00")
            except sqlite3.OperationalError:
                pass 
                
            # Columna: Proveedor (Sustituye a Ubicación)
            try:
                cursor.execute("ALTER TABLE productos ADD COLUMN proveedor TEXT")
            except sqlite3.OperationalError:
                pass 
                
            # --- INSERCIÓN DE DATOS INICIALES ---

            # Insertar usuario administrador si no existe
            cursor.execute("SELECT id FROM usuarios WHERE usuario='admin'")
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO usuarios (usuario, password, rol) VALUES (?, ?, ?)", 
                               ('admin', '1234', 'administrador'))
                
            # Insertar productos de prueba si no existen (Actualizados con los 3 nuevos campos)
            cursor.execute("SELECT id FROM productos LIMIT 1")
            if cursor.fetchone() is None:
                products_to_insert = [
                    # (codigo, nombre, stock, p_venta, p_costo, categoria, stock_min, porc_margen, proveedor)
                    ('LPT001', 'Laptop Gamer X', 10, 850.50, 700.00, 'Electrónica', 5, 20.0, 'Dell Mayorista'),
                    ('MON002', 'Monitor Curvo 27"', 5, 250.75, 200.00, 'Periféricos', 3, 25.0, 'Distribuidor Caracas'),
                    ('MOU003', 'Mouse Inalámbrico RGB', 50, 15.99, 10.00, 'Periféricos', 10, 37.5, 'Logitech Oficial'),
                ]
                # La consulta ahora espera 9 valores
                cursor.executemany("INSERT INTO productos (codigo, nombre, stock, precio_venta, precio_costo, categoria, stock_minimo, porc_margen, proveedor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", products_to_insert)


            conn.commit()
            print(f"Conectado a la DB: {self.db_name}")

        except sqlite3.Error as e:
            print(f"Error al inicializar la base de datos: {e}")
        finally:
            if conn:
                conn.close()

    # --- NUEVOS MÉTODOS PARA OBTENER/GUARDAR LA TASA DE CAMBIO ---
    
    def get_exchange_rate(self):
        """Obtiene la tasa de cambio USD a Bs desde la DB. Devuelve Decimal."""
        result = self.fetch_one("SELECT valor FROM configuracion WHERE clave = 'tasa_usd_bs'")
        if result and result[0] is not None:
            # Asegura que se devuelve como Decimal, redondeado a dos decimales para visualización
            return Decimal(str(result[0])).quantize(Decimal("0.01")) 
        # Valor por defecto si no se encuentra
        return Decimal('36.50') 

    def set_exchange_rate(self, rate: Decimal):
        """Guarda la nueva tasa de cambio USD a Bs en la DB."""
        # Convertimos a float para SQLite (la conversión a Decimal se hace al leer)
        rate_float = float(rate.quantize(Decimal("0.01"))) 
        self.execute_query("INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)", 
                           ('tasa_usd_bs', rate_float))

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
            
            # Obtener nombres de columnas para referencias futuras (opcional, pero útil)
            col_names = [description[0] for description in cursor.description]
            
            for row in cursor.fetchall():
                new_row = list(row)
                for idx, item in enumerate(new_row):
                    # Si el ítem es un float, lo convertimos a Decimal.
                    if isinstance(item, float):
                        try:
                            # Convertimos el float a cadena antes de Decimal para evitar la pérdida de precisión
                            new_row[idx] = Decimal(str(item)).quantize(Decimal("0.01")) 
                        except Exception:
                            new_row[idx] = Decimal('0.00')
                results.append(tuple(new_row))
            
            # Devolvemos los nombres de las columnas junto con los resultados si es necesario, 
            # pero por ahora mantenemos el formato de solo la lista de tuplas.
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
