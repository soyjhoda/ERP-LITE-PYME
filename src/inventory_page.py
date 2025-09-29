import customtkinter as ctk
from tkinter import messagebox, ttk

# Definición de colores
ACCENT_CYAN = "#00FFFF"       
ACCENT_GREEN = "#00c853"      
BACKGROUND_DARK = "#0D1B2A"   
FRAME_MID = "#1B263B"         
FRAME_DARK = "#1B263B"        

class InventoryPage(ctk.CTkFrame):
    """Clase para la página de Inventario, maneja la visualización y búsqueda de productos."""

    def __init__(self, master, db_manager, user_id):
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.user_id = user_id
        
        # 0. CONFIGURACIÓN FORZADA DE ESTILOS TTK ESTÁNDAR
        # SE ELIMINA LA REFERENCIA A "Treeview.Search" para evitar el error.
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
        
        # Se elimina el borde y se ajusta el padding para la tabla
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
        ctk.CTkButton(self.search_frame, text="➕ Añadir Producto", command=lambda: messagebox.showinfo("Info", "Funcionalidad pendiente"),
                      fg_color=ACCENT_GREEN, hover_color="#008a38", height=40).grid(row=0, column=1, padx=(10, 20), pady=10, sticky="e")

        # 3. Frame de la Tabla (Fila 1)
        self.table_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        self.table_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        # 4. Configuración del Treeview (Tabla)
        # IMPORTANTE: SE ELIMINA EL ARGUMENTO 'style="Treeview.Search"'
        self.inventory_tree = ttk.Treeview(self.table_frame, 
                                           columns=("id", "code", "name", "stock", "price", "cost", "category"), 
                                           show='headings') 
        
        # Columnas
        self.inventory_tree.heading("id", text="ID"); self.inventory_tree.column("id", width=50, stretch=ctk.NO)
        self.inventory_tree.heading("code", text="Código"); self.inventory_tree.column("code", width=120, stretch=ctk.NO)
        self.inventory_tree.heading("name", text="Nombre del Producto"); self.inventory_tree.column("name", minwidth=250, stretch=ctk.YES)
        self.inventory_tree.heading("stock", text="Stock"); self.inventory_tree.column("stock", width=80, anchor=ctk.CENTER)
        self.inventory_tree.heading("price", text="Precio Venta"); self.inventory_tree.column("price", width=120, anchor=ctk.E)
        self.inventory_tree.heading("cost", text="Costo"); self.inventory_tree.column("cost", width=120, anchor=ctk.E)
        self.inventory_tree.heading("category", text="Categoría"); self.inventory_tree.column("category", width=150)
        
        self.inventory_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Barra de desplazamiento
        scrollbar = ctk.CTkScrollbar(self.table_frame, command=self.inventory_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=10)
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)
        
        self.load_products()

    def load_products(self):
        """Carga todos los productos desde la base de datos y los inserta en el Treeview."""
        # Limpiar la tabla existente
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        # Obtener todos los productos
        products = self.db.fetch_all("SELECT id, codigo, nombre, stock, precio_venta, precio_costo, categoria FROM productos")
        
        # Insertar los datos en el Treeview
        for product in products:
            # Formato de moneda para Precio Venta y Costo (solo para visualización)
            formatted_product = list(product)
            try:
                formatted_product[4] = f"Bs/{formatted_product[4]:,.2f}" # Precio Venta
                formatted_product[5] = f"Bs/{formatted_product[5]:,.2f}" # Precio Costo
            except (ValueError, TypeError):
                formatted_product[4] = "Bs/0.00" 
                formatted_product[5] = "Bs/0.00" 
            
            self.inventory_tree.insert("", "end", values=formatted_product)

    def search_products(self, event=None):
        """Busca productos en tiempo real basándose en el texto del campo de búsqueda."""
        query = self.search_entry.get().strip()
        
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)

        if not query:
            self.load_products()
            return
        
        sql_query = """
            SELECT id, codigo, nombre, stock, precio_venta, precio_costo, categoria 
            FROM productos 
            WHERE codigo LIKE ? OR nombre LIKE ?
        """
        search_term = f"%{query}%"
        products = self.db.fetch_all(sql_query, (search_term, search_term))

        for product in products:
            formatted_product = list(product)
            try:
                formatted_product[4] = f"Bs/{formatted_product[4]:,.2f}"
                formatted_product[5] = f"Bs/{formatted_product[5]:,.2f}"
            except (ValueError, TypeError):
                 formatted_product[4] = "Bs/0.00" 
                 formatted_product[5] = "Bs/0.00" 
            self.inventory_tree.insert("", "end", values=formatted_product)
            
    def open_add_product_window(self):
        messagebox.showinfo("Pendiente", "Funcionalidad para añadir producto no implementada aún.")