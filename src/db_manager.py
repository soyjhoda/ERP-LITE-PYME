import sqlite3
from sqlite3 import Error
from datetime import datetime
import hashlib 
import os 
import shutil 

DB_FILE = 'profitus.db'

def hash_password(password):
    """Genera un hash SHA-256 para la contraseña."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
    return stored_hash == hash_password(provided_password)

class DatabaseManager:
    """Clase para manejar la conexión y las operaciones de la base de datos SQLite."""
    
    def __init__(self):
        self.db_path = DB_FILE 
        self.conn = None
        self.connect()
        self.create_default_tables() 
        self.initialize_default_config() 

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row 
            print(f"Conectado a la DB: {self.db_path}")
        except Error as e:
            print(f"Error al conectar con SQLite: {e}")
            
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            print("Conexión a la DB cerrada.")

    def execute_query(self, query, params=()):
        if not self.conn:
            print("Error: Conexión a DB no activa.")
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            self.conn.commit()
            return cursor
        except Error as e:
            print(f"Error al ejecutar consulta: {e}")
            self.conn.rollback() 
            return None

    def fetch_one(self, query, params=()):
        if not self.conn:
            return None
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
        except Error as e:
            print(f"Error al obtener una fila: {e}")
            return None

    def fetch_all(self, query, params=()):
        if not self.conn:
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except Error as e:
            print(f"Error al obtener todas las filas: {e}")
            return []

    def _check_and_add_column(self, table_name, column_name, column_type):
        if not self.conn:
            return
        try:
            cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
            columns = [info[1] for info in cursor.fetchall()]
            if column_name not in columns:
                self.execute_query(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                print(f"Columna '{column_name}' añadida a la tabla '{table_name}'.")
        except sqlite3.OperationalError:
            pass
        except Exception as e:
            print(f"Error al verificar/añadir columna {column_name} en {table_name}: {e}")

    def create_default_tables(self):
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                nombre_completo TEXT,
                rol TEXT NOT NULL DEFAULT 'Cajero',
                foto_path TEXT
            )
        """)
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

        self._check_and_add_column('productos', 'proveedor', 'TEXT')
        self._check_and_add_column('productos', 'stock_minimo', 'REAL NOT NULL DEFAULT 0')
        self._check_and_add_column('productos', 'marca', 'TEXT')
        self._check_and_add_column('productos', 'categoria', 'TEXT')
        self._check_and_add_column('usuarios', 'foto_path', 'TEXT') 
        self._check_and_add_column('usuarios', 'nombre_completo', 'TEXT')

        self.execute_query("""
            CREATE TABLE IF NOT EXISTS configuracion (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                total_bs REAL NOT NULL,
                total_usd REAL NOT NULL, 
                tasa_cambio REAL NOT NULL,
                user_id INTEGER,
                payment_method TEXT DEFAULT 'Efectivo',
                amount_received REAL DEFAULT 0.0,
                change_given REAL DEFAULT 0.0,
                mobile_payment_id TEXT DEFAULT NULL,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        """)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS detalles_venta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                nombre_producto TEXT NOT NULL,
                cantidad REAL NOT NULL,
                precio_unitario_usd REAL NOT NULL,
                precio_unitario_bs REAL NOT NULL,
                subtotal_usd REAL NOT NULL,
                subtotal_bs REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)

        self._check_and_add_column('detalles_venta', 'precio_unitario_bs', 'REAL NOT NULL DEFAULT 0.0')
        self._check_and_add_column('detalles_venta', 'subtotal_bs', 'REAL NOT NULL DEFAULT 0.0')
        self._check_and_add_column('detalles_venta', 'precio_unitario_usd', 'REAL NOT NULL DEFAULT 0.0')
        self._check_and_add_column('detalles_venta', 'subtotal_usd', 'REAL NOT NULL DEFAULT 0.0')
        self._check_and_add_column('ventas', 'user_id', 'INTEGER')
        self._check_and_add_column('ventas', 'payment_method', "TEXT DEFAULT 'Efectivo'")
        self._check_and_add_column('ventas', 'amount_received', "REAL DEFAULT 0.0")
        self._check_and_add_column('ventas', 'change_given', "REAL DEFAULT 0.0")
        self._check_and_add_column('ventas', 'mobile_payment_id', "TEXT DEFAULT NULL")

    def initialize_default_config(self):
        hashed_password = hash_password("1234")

        if not self.fetch_one("SELECT id FROM usuarios WHERE username = 'admin'"):
            self.execute_query("INSERT INTO usuarios (username, password, nombre_completo, rol, foto_path) VALUES (?, ?, ?, ?, ?)", 
                                ("admin", hashed_password, "Administrador Principal", "Administrador Total", None)) 
            print("Usuario 'admin' creado con contraseña hasheada y rol 'Administrador Total'.")
        
        if not self.fetch_one("SELECT id FROM productos"):
            products_to_insert = [
                ('P001', 'Laptop Gamer X', 10, 850.50, 600.00, 'Electrónica', 'TechGlobal Inc.', 5, 'Alienware'),
                ('H001', 'Martillo Mango Fibra', 45, 8.00, 5.00, 'Herramientas', 'FerreMax S.A.', 10, 'Truper'),
                ('P002', 'Monitor Curvo 27"', 25, 250.00, 180.00, 'Electrónica', 'TechGlobal Inc.', 10, 'Samsung'),
                ('P003', 'Mouse Inalámbrico', 50, 15.75, 8.50, 'Accesorios', 'AccesoCorp', 20, 'Logitech'),
                ('I001', 'Bombillo LED 10W', 150, 2.50, 1.20, 'Iluminación', 'ElectroWatts', 50, 'Philips'),
            ]
            
            sql_insert = """
                INSERT INTO productos 
                (codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            for prod in products_to_insert:
                self.execute_query(sql_insert, prod)
            print("Productos de prueba insertados con datos USD y campos extendidos.")
        
        if not self.fetch_one("SELECT key FROM configuracion WHERE key = 'exchange_rate'"):
            self.execute_query("INSERT INTO configuracion (key, value) VALUES (?, ?)", 
                                ("exchange_rate", "36.00")) 
            print("Tasa de cambio por defecto (36.00) inicializada.")
        
        if not self.fetch_one("SELECT key FROM configuracion WHERE key = 'company_name'"):
            self.execute_query("INSERT INTO configuracion (key, value) VALUES (?, ?)", 
                                ("company_name", "Mi Empresa Ejemplo")) 
            self.execute_query("INSERT INTO configuracion (key, value) VALUES (?, ?)", 
                                ("company_logo_path", "logo_default.png")) 
            print("Configuración de empresa inicializada.")

    def authenticate_user(self, username, password):
        """Verifica las credenciales del usuario y devuelve el objeto Row si es exitoso (incluye foto_path)."""
        user_row = self.fetch_one("SELECT * FROM usuarios WHERE username = ?", (username,))
        if user_row:
            if verify_password(user_row['password'], password):
                return user_row 
        return None
    
    def get_all_users(self):
        return self.fetch_all("SELECT id, username, nombre_completo, rol, foto_path FROM usuarios")
    
    def create_user(self, username, password, full_name, role, foto_path=None):
        hashed_pw = hash_password(password)
        return self.execute_query(
            "INSERT INTO usuarios (username, password, nombre_completo, rol, foto_path) VALUES (?, ?, ?, ?, ?)", 
            (username, hashed_pw, full_name, role, foto_path)
        )

    def delete_user(self, user_id):
        return self.execute_query("DELETE FROM usuarios WHERE id = ?", (user_id,))
    
    def update_user_role(self, user_id, new_role):
        return self.execute_query("UPDATE usuarios SET rol = ? WHERE id = ?", (new_role, user_id))
    
    def update_user_details(self, user_id, username, full_name, role, foto_path):
        sql = """
            UPDATE usuarios SET 
                username = ?, 
                nombre_completo = ?, 
                rol = ?,
                foto_path = ?
            WHERE id = ?
        """
        return self.execute_query(sql, (username, full_name, role, foto_path, user_id))

    def update_user_password(self, user_id, new_password):
        hashed_pw = hash_password(new_password)
        return self.execute_query("UPDATE usuarios SET password = ? WHERE id = ?", (hashed_pw, user_id))

    def update_user_photo_path(self, user_id, path):
        return self.execute_query("UPDATE usuarios SET foto_path = ? WHERE id = ?", (path, user_id))
        
    def get_user_photo_path(self, user_id):
        row = self.fetch_one("SELECT foto_path FROM usuarios WHERE id = ?", (user_id,))
        return row['foto_path'] if row else None

    def get_company_config(self, key):
        row = self.fetch_one("SELECT value FROM configuracion WHERE key = ?", (key,))
        return row['value'] if row else None

    def set_company_config(self, key, value):
        self.execute_query("""
            INSERT OR REPLACE INTO configuracion (key, value)
            VALUES (?, ?)
        """, (key, str(value)))

    def get_exchange_rate(self):
        row = self.fetch_one("SELECT value FROM configuracion WHERE key = 'exchange_rate'")
        if row:
            try:
                return float(row['value']) 
            except ValueError:
                print("Advertencia: El valor de la tasa de cambio no es un número válido.")
                return 0.0 
        return 0.0 

    def set_exchange_rate(self, rate):
        self.execute_query("""
            INSERT OR REPLACE INTO configuracion (key, value)
            VALUES ('exchange_rate', ?)
        """, (str(rate),))

    def perform_backup(self, destination_path):
        if not self.conn:
            return False, "La conexión a la base de datos no está activa."
            
        try:
            dest_conn = sqlite3.connect(destination_path)
            with dest_conn:
                self.conn.backup(dest_conn)
            dest_conn.close()
            return True, "Backup realizado con éxito."
        
        except sqlite3.Error as e:
            print(f"Error al realizar el backup de SQLite: {e}")
            return False, f"Error de SQLite: {e}"
        except Exception as e:
            print(f"Error inesperado durante el backup: {e}")
            return False, f"Error inesperado: {e}"
            
    def restore_backup(self, source_path):
        if not os.path.exists(source_path):
            return False, "Error: El archivo de backup de origen no fue encontrado."

        main_db_path = self.db_path

        try:
            self.close()
        except Exception as e:
            self.connect() 
            return False, f"Error al intentar cerrar la conexión a la DB: {e}"

        try:
            shutil.copy2(source_path, main_db_path) 
            self.connect() 
            return True, f"Base de datos restaurada exitosamente desde: {source_path}"
            
        except shutil.Error as e:
            self.connect() 
            return False, f"Error de copia de archivo (permisos o en uso): {e}"
            
        except Exception as e:
            self.connect() 
            return False, f"Error inesperado durante la restauración: {e}"

    def get_all_products(self):
        query = "SELECT * FROM productos ORDER BY nombre COLLATE NOCASE ASC"
        return self.fetch_all(query)

    def get_product_by_id(self, product_id):
        query = "SELECT * FROM productos WHERE id = ?"
        return self.fetch_one(query, (product_id,))

    def get_product_by_code(self, codigo):
        query = "SELECT * FROM productos WHERE codigo = ?"
        return self.fetch_one(query, (codigo,))

    def create_product(self, codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca):
        sql = """
            INSERT INTO productos (codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self.execute_query(sql, (codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca))

    def update_product(self, product_id, codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca):
        sql = """
            UPDATE productos SET 
                codigo = ?, nombre = ?, stock = ?, 
                precio_venta = ?, precio_costo = ?, categoria = ?, 
                proveedor = ?, stock_minimo = ?, marca = ?
            WHERE id = ?
        """
        return self.execute_query(sql, (codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca, product_id))

    def delete_product(self, product_id):
        return self.execute_query("DELETE FROM productos WHERE id = ?", (product_id,))

    def process_sale_transaction(self, cart_data, total_final_usd, current_rate, user_id, payment_method='Efectivo', amount_received=0.0, change_given=0.0, mobile_payment_id=None):
        if not self.conn:
            return False, "Conexión a la DB no activa para la venta."

        conn = self.conn
        cursor = conn.cursor()

        for p_id, data in cart_data.items():
            cantidad_vendida = data['cantidad']
            stock_real = data.get('stock_real', 0) 
            if stock_real < cantidad_vendida:
                return False, f"Stock insuficiente (solo quedan {stock_real}) para el producto: {data['nombre']}."

        try:
            fecha_venta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total_final_bs = total_final_usd * current_rate 

            cursor.execute("""
                INSERT INTO ventas (fecha, total_bs, total_usd, tasa_cambio, user_id, payment_method, amount_received, change_given, mobile_payment_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fecha_venta, total_final_bs, total_final_usd, current_rate, user_id, payment_method, amount_received, change_given, mobile_payment_id))

            venta_id = cursor.lastrowid

            for p_id, data in cart_data.items():
                cantidad = data['cantidad']
                precio_unitario_usd = data['precio_usd']
                precio_unitario_bs = precio_unitario_usd * current_rate
                subtotal_usd = cantidad * precio_unitario_usd
                subtotal_bs = cantidad * precio_unitario_bs

                cursor.execute("""
                    INSERT INTO detalles_venta (
                        venta_id, producto_id, nombre_producto, cantidad, 
                        precio_unitario_usd, precio_unitario_bs, subtotal_usd, subtotal_bs
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    venta_id, p_id, data['nombre'], cantidad,
                    precio_unitario_usd, precio_unitario_bs, subtotal_usd, subtotal_bs
                ))

                cursor.execute("""
                    UPDATE productos SET stock = stock - ? WHERE id = ?
                """, (cantidad, p_id))

            conn.commit()
            return True, f"Venta {venta_id} procesada con éxito."

        except Error as e:
            conn.rollback()
            print(f"Error fatal de SQL en la transacción de venta: {e}")
            return False, f"Error de base de datos: {e}"
        except Exception as e:
            conn.rollback()
            print(f"Error inesperado en la transacción de venta: {e}")
            return False, f"Error inesperado: {e}"

    def get_sales_report(self, start_date=None, end_date=None, seller=None):
        query = """
            SELECT ventas.id, ventas.fecha, usuarios.nombre_completo, ventas.total_bs, ventas.total_usd 
            FROM ventas 
            JOIN usuarios ON ventas.user_id = usuarios.id
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND date(ventas.fecha) >= date(?)"
            params.append(start_date)
        if end_date:
            query += " AND date(ventas.fecha) <= date(?)"
            params.append(end_date)
        if seller:
            query += " AND usuarios.nombre_completo = ?"
            params.append(seller)

        query += " ORDER BY ventas.fecha DESC"

        return self.fetch_all(query, tuple(params))

    def get_all_sellers(self):
        query = """
            SELECT DISTINCT nombre_completo FROM usuarios 
            WHERE rol IN ('Vendedor', 'Gerente', 'Administrador Total')
            ORDER BY nombre_completo
        """
        rows = self.fetch_all(query)
        return [row['nombre_completo'] for row in rows] if rows else []
