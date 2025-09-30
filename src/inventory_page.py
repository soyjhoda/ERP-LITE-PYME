import customtkinter as ctk
from tkinter import messagebox, ttk, simpledialog
import re # Necesario para validación de entrada

# Definición de colores
ACCENT_CYAN = "#00FFFF"
ACCENT_GREEN = "#00c853"
BACKGROUND_DARK = "#0D1B2A"
FRAME_MID = "#1B263B"
FRAME_DARK = "#1B263B"
ACCENT_RED = "#e74c3c"

class InventoryPage(ctk.CTkFrame):
    """Clase para la página de Inventario, maneja la visualización y búsqueda de productos."""

    def __init__(self, master, db_manager, user_id):
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.user_id = user_id
        
        # 0. CONFIGURACIÓN FORZADA DE ESTILOS TTK ESTÁNDAR
        style = ttk.Style(self)
        style.theme_use("clam") 
        
        # Aplicamos la configuración al estilo base de TTK "Treeview" y sus encabezados.
        style.configure("Treeview", 
                        background=FRAME_DARK, 
                        foreground="white", 
                        fieldbackground=FRAME_DARK,
                        rowheight=25,
                        font=('Arial', 11))
        
        style.configure("Treeview.Heading", 
                        background="#2c3e50", 
                        foreground="white", 
                        font=('Arial', 11, 'bold'))
        
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})]) 
        # FIN DE LA SOLUCIÓN DEFINITIVA DE ESTILO

        # 1. Configuración de la rejilla principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # 2. Frame de Búsqueda y Botones (Fila 0)
        self.search_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, height=60, corner_radius=10)
        self.search_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        # Campo de Búsqueda
        self.search_entry = ctk.CTkEntry(self.search_frame, 
                                            placeholder_text="Buscar producto por nombre o código...", 
                                            width=350, height=40, 
                                            fg_color="#2c3e50", border_color=ACCENT_CYAN, border_width=1)
        self.search_entry.bind("<KeyRelease>", self.search_products)
        self.search_entry.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Botón Añadir Producto
        ctk.CTkButton(self.search_frame, text="➕ Añadir Producto", command=self.open_add_product_window,
                      fg_color=ACCENT_GREEN, hover_color="#008a38", height=40).grid(row=0, column=1, padx=(10, 20), pady=10, sticky="e")

        # 3. Frame de la Tabla (Fila 1)
        self.table_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        self.table_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        # 4. Configuración del Treeview (Tabla)
        self.inventory_tree = ttk.Treeview(self.table_frame, 
                                            columns=("id", "code", "name", "stock", "stock_min", "price", "cost", "category", "brand", "supplier"), 
                                            show='headings') 
        
        # Columnas actualizadas para incluir nuevos campos
        self.inventory_tree.heading("id", text="ID"); self.inventory_tree.column("id", width=40, stretch=ctk.NO)
        self.inventory_tree.heading("code", text="Código"); self.inventory_tree.column("code", width=100, stretch=ctk.NO)
        self.inventory_tree.heading("name", text="Nombre del Producto"); self.inventory_tree.column("name", minwidth=200, stretch=ctk.YES)
        self.inventory_tree.heading("stock", text="Stock"); self.inventory_tree.column("stock", width=70, anchor=ctk.CENTER)
        self.inventory_tree.heading("stock_min", text="Stock Min."); self.inventory_tree.column("stock_min", width=70, anchor=ctk.CENTER)
        self.inventory_tree.heading("price", text="Venta (USD)"); self.inventory_tree.column("price", width=100, anchor=ctk.E)
        self.inventory_tree.heading("cost", text="Costo (USD)"); self.inventory_tree.column("cost", width=100, anchor=ctk.E)
        self.inventory_tree.heading("category", text="Categoría"); self.inventory_tree.column("category", width=120)
        self.inventory_tree.heading("brand", text="Marca"); self.inventory_tree.column("brand", width=100)
        self.inventory_tree.heading("supplier", text="Proveedor"); self.inventory_tree.column("supplier", width=150)
        
        self.inventory_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Barra de desplazamiento
        scrollbar = ctk.CTkScrollbar(self.table_frame, command=self.inventory_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        self.load_products()

    # --- Métodos de Interfaz y Lógica de Datos ---

    def load_products(self, rate=None): 
        """Carga todos los productos desde la base de datos y los inserta en el Treeview."""
        
        # Limpiar la tabla existente
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        # Obtener todos los productos, incluyendo los nuevos campos
        sql_query = """
            SELECT 
                id, codigo, nombre, stock, stock_minimo, 
                precio_venta, precio_costo, categoria, marca, proveedor 
            FROM productos
        """
        products = self.db.fetch_all(sql_query)
        
        # Insertar los datos en el Treeview
        for product in products:
            # product es un sqlite3.Row, accedemos por nombre
            
            # Chequeo de Stock Mínimo para aplicar tag de color
            stock = product['stock']
            stock_minimo = product['stock_minimo']
            tags = ()
            if stock <= stock_minimo:
                tags = ('min_stock',)
                
            # Formato de moneda para Precio Venta y Costo (Mostrado en USD)
            formatted_product = [
                product['id'],
                product['codigo'],
                product['nombre'],
                f"{stock:g}", # Usar :g para evitar decimales innecesarios (ej. 10.0)
                f"{stock_minimo:g}",
                f"$.{product['precio_venta']:,.2f}", # Precio Venta en USD
                f"$.{product['precio_costo']:,.2f}", # Precio Costo en USD
                product['categoria'] if product['categoria'] else 'N/A',
                product['marca'] if product['marca'] else 'N/A',
                product['proveedor'] if product['proveedor'] else 'N/A',
            ]
            
            # Insertar con el tag si el stock es bajo
            self.inventory_tree.insert("", "end", values=formatted_product, tags=tags)

        # Configurar estilo para alerta de stock mínimo
        self.inventory_tree.tag_configure('min_stock', background=ACCENT_RED, foreground='white')


    def search_products(self, event=None):
        """Busca productos en tiempo real basándose en el texto del campo de búsqueda."""
        query = self.search_entry.get().strip()
        
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        if not query:
            self.load_products()
            return
        
        sql_query = """
            SELECT id, codigo, nombre, stock, stock_minimo, precio_venta, precio_costo, categoria, marca, proveedor 
            FROM productos 
            WHERE codigo LIKE ? OR nombre LIKE ? OR marca LIKE ?
        """
        search_term = f"%{query}%"
        products = self.db.fetch_all(sql_query, (search_term, search_term, search_term))

        for product in products:
            stock = product['stock']
            stock_minimo = product['stock_minimo']
            tags = ()
            if stock <= stock_minimo:
                tags = ('min_stock',)

            formatted_product = [
                product['id'],
                product['codigo'],
                product['nombre'],
                f"{stock:g}",
                f"{stock_minimo:g}",
                f"$.{product['precio_venta']:,.2f}", # USD
                f"$.{product['precio_costo']:,.2f}", # USD
                product['categoria'] if product['categoria'] else 'N/A',
                product['marca'] if product['marca'] else 'N/A',
                product['proveedor'] if product['proveedor'] else 'N/A',
            ]
            self.inventory_tree.insert("", "end", values=formatted_product, tags=tags)
            
    # --- VENTANA PARA AÑADIR NUEVO PRODUCTO ---
    
    def open_add_product_window(self):
        """Abre la ventana modal para añadir un nuevo producto con todos los campos."""
        
        # 1. Crear Toplevel (Ventana Modal)
        self.add_product_window = ctk.CTkToplevel(self)
        self.add_product_window.title("Añadir Nuevo Producto")
        self.add_product_window.geometry("500x700")
        self.add_product_window.transient(self.master.master) # Mantenerla encima de la ventana principal
        self.add_product_window.grab_set() # Bloquear interacción con la ventana principal
        
        # Configuración de la rejilla
        self.add_product_window.grid_columnconfigure(0, weight=1)
        self.add_product_window.configure(fg_color=BACKGROUND_DARK)

        ctk.CTkLabel(self.add_product_window, text="Registro de Producto", 
                     font=ctk.CTkFont(size=20, weight="bold"), text_color=ACCENT_CYAN).grid(row=0, column=0, pady=20)

        # 2. Frame de Entrada de Datos
        input_frame = ctk.CTkFrame(self.add_product_window, fg_color=FRAME_MID, corner_radius=10)
        input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        input_frame.grid_columnconfigure(1, weight=1)

        # Lista de campos y variables de control
        fields = {
            "Código de Producto (único):": ctk.StringVar(),
            "Nombre del Producto:": ctk.StringVar(),
            "Stock Inicial (Unidades):": ctk.StringVar(value="0"),
            "Stock Mínimo (Alerta):": ctk.StringVar(value="0"),
            "Precio de Venta (USD):": ctk.StringVar(),
            "Precio de Costo (USD):": ctk.StringVar(),
            "Marca:": ctk.StringVar(),
        }
        
        # Campo de proveedor (se usará un ComboBox simulado con valores hardcodeados por ahora)
        self.supplier_var = ctk.StringVar(value="Proveedor Principal")
        # Campo de Categoría (ComboBox simulado)
        self.category_var = ctk.StringVar(value="Electrónica")
        
        # Valores de ejemplo para ComboBox (Esto se manejaría con una tabla de proveedores y categorías en una mejora futura)
        supplier_options = ["Proveedor Principal", "TechGlobal Inc.", "FerreMax S.A.", "AccesoCorp", "Otro..."]
        category_options = ["Electrónica", "Herramientas", "Accesorios", "Iluminación", "Hogar", "Otro..."]

        row_idx = 0
        self.entry_widgets = {} # Diccionario para guardar referencias a las entradas de texto

        for label_text, var in fields.items():
            ctk.CTkLabel(input_frame, text=label_text, anchor="w", text_color="white").grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
            
            entry = ctk.CTkEntry(input_frame, textvariable=var, height=30, fg_color="#2c3e50")
            entry.grid(row=row_idx, column=1, padx=10, pady=5, sticky="ew")
            self.entry_widgets[label_text] = entry # Guardamos la referencia
            row_idx += 1
            
        # Campo Proveedor (ComboBox)
        ctk.CTkLabel(input_frame, text="Proveedor:", anchor="w", text_color="white").grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkComboBox(input_frame, variable=self.supplier_var, values=supplier_options, fg_color="#2c3e50", button_color=ACCENT_CYAN, button_hover_color="#00aaff").grid(row=row_idx, column=1, padx=10, pady=5, sticky="ew")
        row_idx += 1
        
        # Campo Categoría (ComboBox)
        ctk.CTkLabel(input_frame, text="Categoría:", anchor="w", text_color="white").grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkComboBox(input_frame, variable=self.category_var, values=category_options, fg_color="#2c3e50", button_color=ACCENT_CYAN, button_hover_color="#00aaff").grid(row=row_idx, column=1, padx=10, pady=5, sticky="ew")
        row_idx += 1
        
        # 3. Botones de Acción
        ctk.CTkButton(self.add_product_window, text="✅ Guardar Producto", command=lambda: self.save_new_product(fields),
                      fg_color=ACCENT_GREEN, hover_color="#008a38", height=40).grid(row=2, column=0, padx=20, pady=(20, 10), sticky="ew")

        ctk.CTkButton(self.add_product_window, text="❌ Cancelar", command=self.add_product_window.destroy,
                      fg_color="#34495e", hover_color="#2c3e50", height=40).grid(row=3, column=0, padx=20, pady=(0, 20), sticky="ew")

    def save_new_product(self, fields):
        """Valida y guarda los datos del nuevo producto en la base de datos."""
        
        # 1. Extracción y Conversión de Datos
        try:
            codigo = fields["Código de Producto (único):"].get().strip().upper()
            nombre = fields["Nombre del Producto:"].get().strip()
            stock = float(fields["Stock Inicial (Unidades):"].get())
            stock_minimo = float(fields["Stock Mínimo (Alerta):"].get())
            precio_venta = float(fields["Precio de Venta (USD):"].get())
            precio_costo = float(fields["Precio de Costo (USD):"].get())
            marca = fields["Marca:"].get().strip()
            
            # ComboBox/Variables
            proveedor = self.supplier_var.get()
            categoria = self.category_var.get()
            
        except ValueError:
            messagebox.showerror("Error de Datos", "Stock, Stock Mínimo, Precio de Venta y Precio de Costo deben ser números válidos.")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Faltan campos por llenar o error de formato: {e}")
            return

        # 2. Validación de Campos Obligatorios y Lógica
        if not all([codigo, nombre]):
            messagebox.showerror("Error de Validación", "El Código y el Nombre del Producto son obligatorios.")
            return

        if precio_venta <= 0 or precio_costo <= 0:
            messagebox.showerror("Error de Validación", "Los precios de Venta y Costo deben ser mayores a cero.")
            return
            
        if stock < 0 or stock_minimo < 0:
            messagebox.showerror("Error de Validación", "El stock y el stock mínimo no pueden ser números negativos.")
            return

        # 3. Inserción en la Base de Datos
        try:
            sql = """
                INSERT INTO productos 
                (codigo, nombre, stock, stock_minimo, precio_venta, precio_costo, marca, proveedor, categoria)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (codigo, nombre, stock, stock_minimo, precio_venta, precio_costo, marca, proveedor, categoria)
            result = self.db.execute_query(sql, params)

            if result:
                messagebox.showinfo("Éxito", f"Producto '{nombre}' ({codigo}) guardado correctamente.")
                self.add_product_window.destroy() # Cerrar la ventana modal
                self.load_products() # Recargar la lista de productos
            else:
                 # Esta parte captura el error si el código ya existe (UNIQUE constraint)
                messagebox.showerror("Error DB", "No se pudo guardar el producto. El código de producto podría ya existir.")

        except Error as e:
            messagebox.showerror("Error de Base de Datos", f"Hubo un error al insertar el producto: {e}")
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error inesperado: {e}")
