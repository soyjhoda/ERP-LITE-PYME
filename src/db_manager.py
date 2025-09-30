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
            # Si hay un error, deshacemos cualquier cambio pendiente (aunque no usemos transacciones explícitas aquí)
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

    def create_default_tables(self):
        """Crea las tablas de usuarios, productos, configuración, ventas y detalles_venta si no existen."""
        
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

        # 3. Tabla de Configuración (para parámetros globales como la Tasa de Cambio)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS configuracion (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        
        # --- TABLAS NUEVAS PARA REGISTRO DE VENTAS ---
        
        # 4. Tabla de Ventas (Encabezado de la factura)
        self.execute_query("""
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                total_bs REAL NOT NULL,
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
                precio_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id),
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        """)
        # ----------------------------------------------
            
    def initialize_default_config(self):
        """Inserta la configuración inicial por defecto."""
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
        self.execute_query("""
            INSERT OR REPLACE INTO configuracion (key, value)
            VALUES ('exchange_rate', ?)
        """, (str(rate),))


    # --- NUEVO MÉTODO TRANSACCIONAL CRUCIAL ---

    def process_sale_transaction(self, cart_data, total_final_bs, current_rate, user_id):
        """
        Ejecuta una transacción atómica para registrar la venta y descontar el stock.
        Si alguna operación falla (ej. stock insuficiente), la transacción se revierte.

        :param cart_data: Diccionario del carrito con {p_id: {'nombre', 'precio', 'cantidad'}}
        :param total_final_bs: Total de la venta en bolívares.
        :param current_rate: Tasa de cambio usada en la venta.
        :param user_id: ID del usuario que registra la venta.
        :return: True si la transacción fue exitosa, False en caso contrario.
        """
        cursor = self.conn.cursor()
        
        # 1. Verificar Stock Mínimo para todos los productos
        for p_id, data in cart_data.items():
            cantidad_vendida = data['cantidad']
            
            stock_data = self.fetch_one("SELECT stock FROM productos WHERE id = ?", (p_id,))
            
            if stock_data is None or stock_data[0] < cantidad_vendida:
                # Si no hay stock suficiente, abortar la venta antes de iniciar la transacción.
                return False, f"Stock insuficiente para el producto ID {p_id}."


        try:
            # INICIO DE LA TRANSACCIÓN
            # SQLite maneja implícitamente la transacción con BEGIN por defecto en cada sentencia,
            # pero hacemos el ROLLBACK/COMMIT explícito para manejar el flujo.

            fecha_venta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # A. Insertar Encabezado de Venta (Tabla 'ventas')
            cursor.execute("""
                INSERT INTO ventas (fecha, total_bs, tasa_cambio, user_id)
                VALUES (?, ?, ?, ?)
            """, (fecha_venta, total_final_bs, current_rate, user_id))
            
            # Obtener el ID de la venta recién insertada (clave para los detalles)
            venta_id = cursor.lastrowid 

            # B. Iterar sobre el carrito para insertar detalles y descontar stock
            for p_id, data in cart_data.items():
                cantidad = data['cantidad']
                precio_unitario = data['precio']
                nombre = data['nombre']
                subtotal = cantidad * precio_unitario

                # B.1. Insertar Detalle de Venta (Tabla 'detalles_venta')
                cursor.execute("""
                    INSERT INTO detalles_venta (venta_id, producto_id, nombre_producto, cantidad, precio_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (venta_id, p_id, nombre, cantidad, precio_unitario, subtotal))

                # B.2. Descontar Stock (Tabla 'productos')
                cursor.execute("""
                    UPDATE productos SET stock = stock - ? WHERE id = ?
                """, (cantidad, p_id))

            # FIN DE LA TRANSACCIÓN: Confirmar todos los cambios
            self.conn.commit()
            return True, "Venta procesada con éxito y stock descontado."

        except Error as e:
            # Si ocurre cualquier error, revertir los cambios
            self.conn.rollback() 
            print(f"Error fatal en la transacción de venta: {e}")
            return False, f"Error de base de datos: {e}"
        except Exception as e:
            self.conn.rollback()
            return False, f"Error inesperado: {e}"
