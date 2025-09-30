import sqlite3
from sqlite3 import Error
import os
from datetime import datetime

DB_FILE = 'profitus.db'

class DatabaseManager:
    """Clase para manejar la conexión y las operaciones de la base de datos SQLite."""
    
    def __init__(self):
        """Inicializa la conexión con la base de datos y crea tablas si no existen."""
        self.conn = None
        self.connect()
        self.create_default_tables() 
        self.initialize_default_config() 

    def connect(self):
        """Establece la conexión con la base de datos."""
        try:
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
            self.conn.rollback() 
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

    def _check_and_add_column(self, table_name, column_name, column_type):
        """Verifica si una columna existe y la añade si no."""
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
                rol TEXT NOT NULL DEFAULT 'empleado'
            )
        """)
        
        # 2. Tabla de Productos 
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

        # 3. Tabla de Configuración 
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
        # Nota: Revisamos y añadimos los campos de Bolívares que nos faltaban
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS detalles_venta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                nombre_producto TEXT NOT NULL,
                cantidad REAL NOT NULL,
                precio_unitario_usd REAL NOT NULL,-- El precio base en USD
                precio_unitario_bs REAL NOT NULL,-- El precio unitario en Bs al momento de la venta
                subtotal_usd REAL NOT NULL,-- Subtotal en USD
                subtotal_bs REAL NOT NULL, -- Subtotal en Bs
                FOREIGN KEY (venta_id) REFERENCES ventas(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)
        
        # Migración: Añadir campos de Bs a detalles_venta si no existen
        self._check_and_add_column('detalles_venta', 'precio_unitario_bs', 'REAL NOT NULL DEFAULT 0.0')
        self._check_and_add_column('detalles_venta', 'subtotal_bs', 'REAL NOT NULL DEFAULT 0.0')
        # También renombramos/alineamos el campo 'precio_unitario' antiguo a 'precio_unitario_usd'
        # Nota: SQLite no permite renombrar fácilmente, asumiremos que los campos 'precio_unitario' y 'subtotal' 
        # de la versión anterior ya fueron tratados como USD por la aplicación, y nos enfocaremos en 
        # asegurar los campos 'precio_unitario_usd' y 'subtotal_usd'
        # Haremos una verificación para asegurar que los campos base de USD existen también
        self._check_and_add_column('detalles_venta', 'precio_unitario_usd', 'REAL NOT NULL DEFAULT 0.0')
        self._check_and_add_column('detalles_venta', 'subtotal_usd', 'REAL NOT NULL DEFAULT 0.0')
        
        # Aseguramos que los campos viejos no interfieran, si existían antes de la migración
        
        
    def initialize_default_config(self):
        """Inserta la configuración inicial por defecto."""
        # Insertar usuario administrador por defecto si no existe
        if not self.fetch_one("SELECT id FROM usuarios WHERE username = 'admin'"):
            self.execute_query("INSERT INTO usuarios (username, password, rol) VALUES (?, ?, ?)", 
                               ("admin", "1234", "admin"))
            print("Usuario 'admin' creado.")
            
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

    # --- Funciones Específicas para Tasa de Cambio ---

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


    # --- MÉTODO TRANSACCIONAL CRUCIAL ---

    def process_sale_transaction(self, cart_data, total_final_usd, current_rate, user_id):
        """
        Ejecuta una transacción atómica para registrar la venta y descontar el stock.
        
        :param cart_data: Diccionario del carrito con {p_id: {'nombre', 'precio_usd', 'stock_real', 'cantidad'}}
        :param total_final_usd: Total de la venta calculado en USD.
        :param current_rate: Tasa de cambio usada en la venta.
        :param user_id: ID del usuario que registra la venta.
        :return: (True, "Mensaje de éxito") o (False, "Mensaje de error").
        """
        # Usaremos una nueva conexión local para esta transacción para garantizar el rollback/commit
        # Aunque la clase ya usa self.conn, lo manejaremos con un cursor local y explícito
        
        conn = self.conn
        cursor = conn.cursor()
        
        # 1. Chequeo de stock (Reconfirmar justo antes de la transacción)
        for p_id, data in cart_data.items():
            cantidad_vendida = data['cantidad']
            
            # Usamos el stock_real del carrito, que se cargó desde la DB inicialmente
            stock_real = data['stock_real'] 
            
            # El stock disponible es el real menos la cantidad que ya está en el carrito (incluyendo esta venta)
            # Como la vista ya validó el stock, este es un doble chequeo de seguridad.
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

    # --- Funciones CRUD de Productos ---
    # (El resto de tus métodos de DB, como insert_product, get_product_by_id, etc. irían aquí)
    # ...
