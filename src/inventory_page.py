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
        ctk.CTkButton(self.search_frame, text="➕ Añadir Producto", command=self.open_add_product_window,
                      fg_color=ACCENT_GREEN, hover_color="#008a38", height=40).grid(row=0, column=1, padx=(10, 20), pady=10, sticky="e")

        # 3. Frame de la Tabla (Fila 1)
        self.table_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        self.table_frame.grid(row=1, column=0, padx=20, pady=(10, 20), sticky="nsew")
        self.table_frame.grid_rowconfigure(0, weight=1)
        self.table_frame.grid_columnconfigure(0, weight=1)

        # 4. Configuración del Treeview (Tabla)
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

    def load_products(self, rate=None): # <--- ACEPTA EL ARGUMENTO OPCIONAL 'rate'
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
import customtkinter as ctk
from tkinter import messagebox, ttk
from PIL import Image

# --- Importaciones de las Vistas ---
from .pos_page import PosPage 
from .inventory_page import InventoryPage
from .config_page import ConfigPage
# -----------------------------------

# Definición de colores 
ACCENT_CYAN = "#00FFFF"       
ACCENT_GREEN = "#00c853"       
BACKGROUND_DARK = "#0D1B2A"   
FRAME_MID = "#1B263B"         
LOGO_PATH = "assets/images/logo.png"


class DashboardFrame(ctk.CTkFrame):
    """Contenedor principal que aloja la navegación, el menú y el contenido de la aplicación."""
    def __init__(self, master, db_manager, user_id):
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.current_user_id = user_id
        
        self.pages = {}
        self.current_page = None

        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # 1. BARRA DE NAVEGACIÓN (Columna 0)
        self.navigation_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, width=200, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        self.navigation_frame.grid_rowconfigure(7, weight=1) 
        
        # Logo
        try:
             logo_img = ctk.CTkImage(light_image=Image.open(LOGO_PATH),
                                     dark_image=Image.open(LOGO_PATH),
                                     size=(40, 40)) 
             ctk.CTkLabel(self.navigation_frame, image=logo_img, text=" PROFITUS", 
                          font=ctk.CTkFont(size=20, weight="bold"), 
                          text_color=ACCENT_CYAN, compound="left").grid(row=0, column=0, padx=20, pady=(20, 10))
        except FileNotFoundError:
             ctk.CTkLabel(self.navigation_frame, text="PROFITUS", 
                          font=ctk.CTkFont(size=20, weight="bold"), 
                          text_color=ACCENT_CYAN).grid(row=0, column=0, padx=20, pady=(20, 10))

        # Título del Menú
        ctk.CTkLabel(self.navigation_frame, text="MENÚ", font=ctk.CTkFont(size=14), text_color="gray60").grid(row=1, column=0, padx=20, pady=(20, 5), sticky="w")
        
        button_args = {
            "corner_radius": 5, "height": 40, 
            "fg_color": "transparent", "text_color": "white",
            "hover_color": "#2c3e50", "anchor": "w",
            "font": ctk.CTkFont(size=15)
        }
        
        # Botones de navegación
        self.home_button = ctk.CTkButton(self.navigation_frame, text="🏠 Home",
                                         command=lambda: self.select_frame_by_name("home"), **button_args)
        self.home_button.grid(row=2, column=0, sticky="ew", padx=10, pady=2)
        
        self.inventory_button = ctk.CTkButton(self.navigation_frame, text="📦 Inventario",
                                              command=lambda: self.select_frame_by_name("inventory"), **button_args)
        self.inventory_button.grid(row=3, column=0, sticky="ew", padx=10, pady=2)
        
        self.pos_button = ctk.CTkButton(self.navigation_frame, text="🛒 PDV (POS)",
                                         command=lambda: self.select_frame_by_name("pos"), **button_args)
        self.pos_button.grid(row=4, column=0, sticky="ew", padx=10, pady=2)
        
        self.config_button = ctk.CTkButton(self.navigation_frame, text="⚙️ Configuración",
                                            command=lambda: self.select_frame_by_name("config"), **button_args)
        self.config_button.grid(row=5, column=0, sticky="ew", padx=10, pady=2)
        
        # --- NUEVA SECCIÓN: INDICADOR DE TASA DE CAMBIO (Bs/USD) ---
        self.rate_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        self.rate_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=(15, 5))
        self.rate_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.rate_frame, text="TASA (Bs/USD)", 
                     font=ctk.CTkFont(size=12, weight="bold"), 
                     text_color="gray70").grid(row=0, column=0, sticky="w")
        
        self.exchange_rate_label = ctk.CTkLabel(self.rate_frame, 
                                                text="Cargando...", 
                                                font=ctk.CTkFont(size=16, weight="bold"), 
                                                text_color=ACCENT_GREEN)
        self.exchange_rate_label.grid(row=1, column=0, sticky="w")
        # -----------------------------------------------------------
        
        # Botón de Cerrar Sesión
        ctk.CTkButton(self.navigation_frame, text="❌ Cerrar Sesión", 
                      command=master.destroy, 
                      fg_color="#c0392b", hover_color="#a13024",
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=8, column=0, sticky="ew", padx=10, pady=(10, 20))
        
        # 2. ÁREA DE CONTENIDO (Columna 1)
        self.content_container = ctk.CTkFrame(self, fg_color=BACKGROUND_DARK, corner_radius=0)
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        # Cargar y mostrar la tasa de cambio inicial
        self.update_exchange_rate_label()

        # 3. INICIALIZACIÓN DE PÁGINAS
        self._create_pages()
        
        self.select_frame_by_name("home")

    def update_exchange_rate_label(self):
        """Carga la tasa de cambio actual desde la base de datos y actualiza el label."""
        try:
            # Llama al nuevo método de la base de datos
            rate = self.db.get_exchange_rate() 
            # Formatea
            formatted_rate = f"Bs. {rate:,.2f}" 
            self.exchange_rate_label.configure(text=formatted_rate)
            return rate 
        except Exception as e:
            print(f"Error al cargar la tasa de cambio: {e}")
            self.exchange_rate_label.configure(text="Error de carga")
            return None


    def _create_pages(self):
        """Instancia todas las páginas y las guarda en el diccionario self.pages."""

        # 1. Página de Inicio (Home)
        home_frame = ctk.CTkFrame(self.content_container, fg_color=BACKGROUND_DARK)
        home_frame.grid_columnconfigure(0, weight=1)
        home_frame.grid_rowconfigure(0, weight=1)
        
        welcome_frame = ctk.CTkFrame(home_frame, fg_color="transparent")
        welcome_frame.grid(row=0, column=0, sticky="nsew")
        welcome_frame.grid_columnconfigure(0, weight=1)
        welcome_frame.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(welcome_frame, text=f"Bienvenido al Dashboard", 
                     font=ctk.CTkFont(size=30, weight="bold"), text_color=ACCENT_CYAN).grid(row=0, column=0, pady=(100, 5))
        ctk.CTkLabel(welcome_frame, text="Usa el menú lateral para navegar.", 
                     font=ctk.CTkFont(size=16), text_color="gray70").grid(row=1, column=0, pady=(0, 100))
        
        self.pages["home"] = home_frame

        # 2. Páginas funcionales
        # La InventoryPage ya no necesita argumentos extra en su constructor original
        self.pages["inventory"] = InventoryPage(self.content_container, self.db, self.current_user_id)
        # La PosPage ya no necesita argumentos extra en su constructor original
        self.pages["pos"] = PosPage(self.content_container, self.db, self.current_user_id)
        # IMPORTANTE: Pasamos el método de actualización al constructor de ConfigPage
        self.pages["config"] = ConfigPage(self.content_container, self.db, self.current_user_id, self.update_exchange_rate_label)


    def select_frame_by_name(self, name):
        """Muestra la página seleccionada y oculta las demás."""
        
        # Desactivar color de todos los botones
        self.home_button.configure(fg_color="transparent")
        self.inventory_button.configure(fg_color="transparent")
        self.pos_button.configure(fg_color="transparent")
        self.config_button.configure(fg_color="transparent")

        for page_name, page_frame in self.pages.items():
            if page_name == name:
                # Si es Inventario, llamar a load_products para recargar datos
                if page_name == "inventory":
                    try:
                        # Obtenemos la tasa actual (aunque no la use, es bueno mantener el llamado)
                        current_rate = self.update_exchange_rate_label() 
                        
                        # Llama a load_products (ahora preparado para aceptar 'current_rate')
                        page_frame.load_products(current_rate)
                    except AttributeError:
                        pass
                
                # Si es POS, actualizar la tasa localmente
                elif page_name == "pos":
                    # Cargamos la tasa actual del Dashboard
                    current_rate = self.update_exchange_rate_label()
                    # Si el PosPage tiene un método para actualizar la tasa, lo llamamos
                    if hasattr(page_frame, 'update_rate'):
                        page_frame.update_rate(current_rate)

                
                page_frame.grid(row=0, column=0, sticky="nsew")
                self.current_page = page_frame
                
                # Activar color del botón
                if name == "home":
                    self.home_button.configure(fg_color="#2c3e50")
                elif name == "inventory":
                    self.inventory_button.configure(fg_color="#2c3e50")
                elif name == "pos":
                    self.pos_button.configure(fg_color="#2c3e50")
                elif name == "config":
                    self.config_button.configure(fg_color="#2c3e50")
            else:
                page_frame.grid_forget()
