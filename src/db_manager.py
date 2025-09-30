import sqlite3
from sqlite3 import Error
from datetime import datetime
import hashlib 
import os # Importado para manejo de archivos
import shutil # Importado para copiar/reemplazar archivos

# Nombre del archivo de la base de datos
DB_FILE = 'profitus.db'

# --- Funciones de Seguridad ---

def hash_password(password):
    """Genera un hash SHA-256 para la contraseña."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(stored_hash, provided_password):
    """Verifica si la contraseña proporcionada coincide con el hash almacenado."""
    return stored_hash == hash_password(provided_password)

# ----------------------------

class DatabaseManager:
    """Clase para manejar la conexión y las operaciones de la base de datos SQLite."""
    
    def __init__(self):
        """Inicializa la conexión con la base de datos y crea tablas si no existen."""
        self.db_path = DB_FILE # Guardamos la ruta del archivo principal
        self.conn = None
        self.connect()
        self.create_default_tables() 
        self.initialize_default_config() 

    def connect(self):
        """Establece la conexión con la base de datos."""
        try:
            # Conexión principal
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre
            print(f"Conectado a la DB: {self.db_path}")
        except Error as e:
            print(f"Error al conectar con SQLite: {e}")
            
    def close(self):
        """Cierra la conexión con la base de datos."""
        if self.conn:
            self.conn.close()
            self.conn = None # Establecer a None para indicar que está cerrada
            print("Conexión a la DB cerrada.")

    def execute_query(self, query, params=()):
        """Ejecuta consultas de modificación (INSERT, UPDATE, DELETE)."""
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
        """Ejecuta consultas de selección y devuelve una sola fila."""
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
        """Ejecuta consultas de selección y devuelve todas las filas."""
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
        """Verifica si una columna existe y la añade si no. (Para migraciones)"""
        if not self.conn: return
        try:
            # Intenta seleccionar la columna para ver si existe
            self.conn.execute(f"SELECT {column_name} FROM {table_name} LIMIT 1")
        except sqlite3.OperationalError:
            # Si la columna no existe (OperationalError), la añadimos.
            self.execute_query(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            print(f"Columna '{column_name}' añadida a la tabla '{table_name}'.")

    def create_default_tables(self):
        """Crea las tablas y asegura la existencia de los nuevos campos de producto."""
        
        # 1. Tabla de Usuarios
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                nombre_completo TEXT,
                rol TEXT NOT NULL DEFAULT 'Cajero'
            )
        """)
        
        # 2. Tabla de Productos (precio_venta y precio_costo siempre en USD)
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

        # Añadir los nuevos campos a la tabla de productos si no existen (Manejo de migraciones)
        self._check_and_add_column('productos', 'proveedor', 'TEXT')
        self._check_and_add_column('productos', 'stock_minimo', 'REAL NOT NULL DEFAULT 0')
        self._check_and_add_column('productos', 'marca', 'TEXT')
        self._check_and_add_column('productos', 'categoria', 'TEXT')

        # 3. Tabla de Configuración (Nombre, Logo, Tasa de Cambio)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS configuracion (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # 4. Tabla de Ventas (Encabezado de la factura)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                total_bs REAL NOT NULL,
                total_usd REAL NOT NULL, 
                tasa_cambio REAL NOT NULL,
                user_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        """)
        
        # 5. Tabla de Detalles de Venta (Líneas de productos en la factura)
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
        
        # Migración: Aseguramos que los campos de moneda existen en detalles_venta
        self._check_and_add_column('detalles_venta', 'precio_unitario_bs', 'REAL NOT NULL DEFAULT 0.0')
        self._check_and_add_column('detalles_venta', 'subtotal_bs', 'REAL NOT NULL DEFAULT 0.0')
        self._check_and_add_column('detalles_venta', 'precio_unitario_usd', 'REAL NOT NULL DEFAULT 0.0')
        self._check_and_add_column('detalles_venta', 'subtotal_usd', 'REAL NOT NULL DEFAULT 0.0')
        
        # Aseguramos que la tabla de Ventas tiene el user_id
        self._check_and_add_column('ventas', 'user_id', 'INTEGER')
        # Aseguramos que la tabla de Usuarios tiene el nombre_completo
        self._check_and_add_column('usuarios', 'nombre_completo', 'TEXT')
            
    def initialize_default_config(self):
        """Inserta la configuración inicial por defecto (Admin, productos de prueba, tasa de cambio)."""
        
        # Hash de la contraseña "1234"
        hashed_password = hash_password("1234")

        # Insertar usuario administrador por defecto si no existe
        if not self.fetch_one("SELECT id FROM usuarios WHERE username = 'admin'"):
            self.execute_query("INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)", 
                               ("admin", hashed_password, "Administrador Principal", "Administrador Total"))
            print("Usuario 'admin' creado con contraseña hasheada y rol 'Administrador Total'.")
            
        # Insertar productos de prueba si no hay ninguno
        if not self.fetch_one("SELECT id FROM productos"):
            # DATOS DE PRUEBA ACTUALIZADOS A USD Y NUEVOS CAMPOS
            products_to_insert = [
                # codigo, nombre, stock, precio_venta (USD), precio_costo (USD), categoria, proveedor, stock_minimo, marca
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
            
        # Insertar Tasa de Cambio por defecto (si no existe)
        if not self.fetch_one("SELECT key FROM configuracion WHERE key = 'exchange_rate'"):
            self.execute_query("INSERT INTO configuracion (key, value) VALUES (?, ?)", 
                               ("exchange_rate", "36.00")) # Valor por defecto
            print("Tasa de cambio por defecto (36.00) inicializada.")
            
        # Insertar Nombre y Logo de la Empresa por defecto (si no existen)
        if not self.fetch_one("SELECT key FROM configuracion WHERE key = 'company_name'"):
            self.execute_query("INSERT INTO configuracion (key, value) VALUES (?, ?)", 
                               ("company_name", "Mi Empresa Ejemplo")) 
            self.execute_query("INSERT INTO configuracion (key, value) VALUES (?, ?)", 
                               ("company_logo_path", "logo_default.png")) # Ruta de logo por defecto
            print("Configuración de empresa inicializada.")


    # --- Funciones Específicas de Usuarios y Autenticación ---

    def authenticate_user(self, username, password):
        """Verifica las credenciales del usuario y devuelve el objeto Row si es exitoso."""
        user_row = self.fetch_one("SELECT * FROM usuarios WHERE username = ?", (username,))
        
        if user_row:
            # Verifica la contraseña hasheada
            if verify_password(user_row['password'], password):
                return user_row # Retorna el objeto Row del usuario
        return None
    
    def get_all_users(self):
        """Devuelve todos los usuarios registrados."""
        return self.fetch_all("SELECT id, username, nombre_completo, rol FROM usuarios")
    
    def create_user(self, username, password, full_name, role):
        """Crea un nuevo usuario con la contraseña hasheada."""
        hashed_pw = hash_password(password)
        return self.execute_query(
            "INSERT INTO usuarios (username, password, nombre_completo, rol) VALUES (?, ?, ?, ?)", 
            (username, hashed_pw, full_name, role)
        )

    def delete_user(self, user_id):
        """Elimina un usuario por su ID."""
        return self.execute_query("DELETE FROM usuarios WHERE id = ?", (user_id,))
    
    def update_user_role(self, user_id, new_role):
        """Actualiza el rol de un usuario existente."""
        return self.execute_query("UPDATE usuarios SET rol = ? WHERE id = ?", (new_role, user_id))
    
    def update_user_password(self, user_id, new_password):
        """Actualiza la contraseña de un usuario (hasheada)."""
        hashed_pw = hash_password(new_password)
        return self.execute_query("UPDATE usuarios SET password = ? WHERE id = ?", (hashed_pw, user_id))

    # --- Funciones Específicas de Configuración ---
    
    def get_company_config(self, key):
        """Obtiene un valor de configuración (ej: company_name, company_logo_path)."""
        row = self.fetch_one("SELECT value FROM configuracion WHERE key = ?", (key,))
        return row['value'] if row else None

    def set_company_config(self, key, value):
        """Guarda o actualiza un valor de configuración."""
        self.execute_query("""
            INSERT OR REPLACE INTO configuracion (key, value)
            VALUES (?, ?)
        """, (key, str(value)))

    def get_exchange_rate(self):
        """Obtiene la tasa de cambio actual desde la tabla de configuración."""
        row = self.fetch_one("SELECT value FROM configuracion WHERE key = 'exchange_rate'")
        if row:
            try:
                return float(row['value']) 
            except ValueError:
                print("Advertencia: El valor de la tasa de cambio no es un número válido.")
                return 0.0 # Valor por defecto seguro
        return 0.0 # Valor por defecto seguro

    def set_exchange_rate(self, rate):
        """Guarda o actualiza la tasa de cambio en la tabla de configuración."""
        self.execute_query("""
            INSERT OR REPLACE INTO configuracion (key, value)
            VALUES ('exchange_rate', ?)
        """, (str(rate),))

    # --- Función de Backup de la DB (Exportar) ---
    def perform_backup(self, destination_path):
        """
        Realiza una copia de seguridad (backup) de la base de datos actual 
        en la ruta de destino especificada.
        """
        if not self.conn:
            return False, "La conexión a la base de datos no está activa."
            
        try:
            # 1. Crear una nueva conexión a la ruta de destino
            dest_conn = sqlite3.connect(destination_path)
            
            # 2. Usar el método backup() de SQLite para copiar los datos
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
            
    # --- FUNCIÓN NUEVA: Restauración de la DB (Importar) ---
    def restore_backup(self, source_path):
        """
        Restaura la base de datos principal copiando el archivo de backup 
        desde la ruta especificada. Cierra la conexión actual antes de copiar.
        """
        # 1. Verificar si el archivo de origen existe
        if not os.path.exists(source_path):
            return False, "Error: El archivo de backup de origen no fue encontrado."

        # 2. Obtener la ruta del archivo principal (profitus.db)
        main_db_path = self.db_path

        # 3. Intentar cerrar la conexión a la base de datos (CRUCIAL para poder reemplazar el archivo)
        try:
            self.close() # Llama a la función 'close' que también pone self.conn = None
        except Exception as e:
            # Si hay un error al cerrar, intentamos reabrir por si acaso y reportamos el error
            self.connect() 
            return False, f"Error al intentar cerrar la conexión a la DB: {e}"

        # 4. Realizar la copia del archivo (reemplazando el archivo actual)
        try:
            # shutil.copy2 copia el archivo, incluyendo metadatos, y reemplaza el destino.
            shutil.copy2(source_path, main_db_path) 

            # 5. Volver a abrir la conexión (preparación para el siguiente uso)
            self.connect() 
            
            return True, f"Base de datos restaurada exitosamente desde: {source_path}"
            
        except shutil.Error as e:
            self.connect() # Reabrir conexión por si acaso
            return False, f"Error de copia de archivo (permisos o en uso): {e}"
            
        except Exception as e:
            self.connect() # Reabrir conexión por si acaso
            return False, f"Error inesperado durante la restauración: {e}"

    # --- Funciones CRUD de Productos (Implementadas) ---
    
    def get_all_products(self):
        """Obtiene todos los productos, ordenados por nombre."""
        query = "SELECT * FROM productos ORDER BY nombre COLLATE NOCASE ASC"
        return self.fetch_all(query)

    def get_product_by_id(self, product_id):
        """Obtiene un producto por su ID."""
        query = "SELECT * FROM productos WHERE id = ?"
        return self.fetch_one(query, (product_id,))

    def get_product_by_code(self, codigo):
        """Obtiene un producto por su código (para búsquedas rápidas)."""
        query = "SELECT * FROM productos WHERE codigo = ?"
        return self.fetch_one(query, (codigo,))

    def create_product(self, codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca):
        """Crea un nuevo producto en la DB. Todos los precios son en USD."""
        sql = """
            INSERT INTO productos (codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # precio_venta y precio_costo deben ser floats (USD)
        return self.execute_query(sql, (codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca))

    def update_product(self, product_id, codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca):
        """Actualiza todos los campos de un producto existente. Todos los precios son en USD."""
        sql = """
            UPDATE productos SET 
                codigo = ?, nombre = ?, stock = ?, 
                precio_venta = ?, precio_costo = ?, categoria = ?, 
                proveedor = ?, stock_minimo = ?, marca = ?
            WHERE id = ?
        """
        return self.execute_query(sql, (codigo, nombre, stock, precio_venta, precio_costo, categoria, proveedor, stock_minimo, marca, product_id))

    def delete_product(self, product_id):
        """Elimina un producto por su ID."""
        return self.execute_query("DELETE FROM productos WHERE id = ?", (product_id,))

    # --- MÉTODO TRANSACCIONAL CRUCIAL ---

    def process_sale_transaction(self, cart_data, total_final_usd, current_rate, user_id):
        """
        Ejecuta una transacción atómica para registrar la venta y descontar el stock.
        """
        if not self.conn:
            return False, "Conexión a la DB no activa para la venta."

        conn = self.conn
        cursor = conn.cursor()
        
        # 1. Chequeo de stock (Reconfirmar justo antes de la transacción)
        for p_id, data in cart_data.items():
            cantidad_vendida = data['cantidad']
            # NOTA: stock_real debe ser pasado desde la capa de la aplicación (UI)
            stock_real = data.get('stock_real', 0) 
            
            if stock_real < cantidad_vendida:
                return False, f"Stock insuficiente (solo quedan {stock_real}) para el producto: {data['nombre']}."

        try:
            # INICIO DE LA TRANSACCIÓN
            fecha_venta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            total_final_bs = total_final_usd * current_rate # Calcular total en BsF
            
            # A. Insertar Encabezado de Venta (Tabla 'ventas')
            cursor.execute("""
                INSERT INTO ventas (fecha, total_bs, total_usd, tasa_cambio, user_id)
                VALUES (?, ?, ?, ?, ?)
            """, (fecha_venta, total_final_bs, total_final_usd, current_rate, user_id))
            
            venta_id = cursor.lastrowid 

            # B. Iterar sobre el carrito para insertar detalles y descontar stock
            for p_id, data in cart_data.items():
                cantidad = data['cantidad']
                precio_unitario_usd = data['precio_usd'] 
                
                # Calcular valores en Bs
                precio_unitario_bs = precio_unitario_usd * current_rate
                subtotal_usd = cantidad * precio_unitario_usd
                subtotal_bs = cantidad * precio_unitario_bs

                # B.1. Insertar Detalle de Venta (Tabla 'detalles_venta')
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

                # B.2. Descontar Stock (Tabla 'productos')
                cursor.execute("""
                    UPDATE productos SET stock = stock - ? WHERE id = ?
                """, (cantidad, p_id))
            
            # FIN DE LA TRANSACCIÓN: Confirmar todos los cambios
            conn.commit()
            return True, f"Venta {venta_id} procesada con éxito."

        except Error as e:
            # Si ocurre cualquier error de SQL, revertir los cambios
            conn.rollback() 
            print(f"Error fatal de SQL en la transacción de venta: {e}")
            return False, f"Error de base de datos: {e}"
            
        except Exception as e:
            # Si ocurre cualquier otro error, revertir los cambios
            conn.rollback()
            print(f"Error inesperado en la transacción de venta: {e}")
            return False, f"Error inesperado: {e}"
