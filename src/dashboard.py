import customtkinter as ctk
from tkinter import messagebox, ttk
from PIL import Image

# --- Importaciones de las Vistas ---
from .pos_page import PosPage 
from .inventory_page import InventoryPage
from .config_page import ConfigPage # Usaremos este nombre por ahora, pero será nuestro AdminPanel
# -----------------------------------

# Definición de colores 
ACCENT_CYAN = "#00FFFF"
ACCENT_GREEN = "#00c853"
BACKGROUND_DARK = "#0D1B2A"
FRAME_MID = "#1B263B"
LOGO_PATH = "assets/images/logo.png"


class DashboardFrame(ctk.CTkFrame):
    """Contenedor principal que aloja la navegación, el menú y el contenido de la aplicación."""
    # ACEPTAMOS EL NUEVO ARGUMENTO: user_role
    def __init__(self, master, db_manager, user_id, user_role):
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.current_user_id = user_id
        self.current_user_role = user_role # ¡NUEVO! Guardamos el rol del usuario
        
        self.pages = {}
        self.current_page = None

        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # 1. BARRA DE NAVEGACIÓN (Columna 0)
        self.navigation_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, width=200, corner_radius=0)
        self.navigation_frame.grid(row=0, column=0, sticky="nsew")
        
        # El número de fila final se ajusta para el botón de cerrar sesión
        self.navigation_frame.grid_rowconfigure(7, weight=1) 
        
        # Logo y Título
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

        # Indicador de Rol
        ctk.CTkLabel(self.navigation_frame, text=f"Rol: {self.current_user_role}", 
                     font=ctk.CTkFont(size=12, weight="bold"), 
                     text_color=ACCENT_GREEN if self.current_user_role in ("Administrador Total", "Gerente") else "gray70"
                     ).grid(row=1, column=0, padx=20, pady=(0, 10), sticky="w")
        
        # Título del Menú
        ctk.CTkLabel(self.navigation_frame, text="MENÚ", font=ctk.CTkFont(size=14), text_color="gray60").grid(row=2, column=0, padx=20, pady=(20, 5), sticky="w")
        
        button_args = {
            "corner_radius": 5, "height": 40, 
            "fg_color": "transparent", "text_color": "white",
            "hover_color": "#2c3e50", "anchor": "w",
            "font": ctk.CTkFont(size=15)
        }
        
        # Botones de navegación (las filas comienzan en 3)
        self.home_button = ctk.CTkButton(self.navigation_frame, text="🏠 Home",
                                         command=lambda: self.select_frame_by_name("home"), **button_args)
        self.home_button.grid(row=3, column=0, sticky="ew", padx=10, pady=2)
        
        self.inventory_button = ctk.CTkButton(self.navigation_frame, text="📦 Inventario",
                                             command=lambda: self.select_frame_by_name("inventory"), **button_args)
        self.inventory_button.grid(row=4, column=0, sticky="ew", padx=10, pady=2)
        
        self.pos_button = ctk.CTkButton(self.navigation_frame, text="🛒 PDV (POS)",
                                         command=lambda: self.select_frame_by_name("pos"), **button_args)
        self.pos_button.grid(row=5, column=0, sticky="ew", padx=10, pady=2)
        
        self.config_button = ctk.CTkButton(self.navigation_frame, text="⚙️ Configuración",
                                             command=lambda: self.select_frame_by_name("config"), **button_args)
        # El botón de configuración se posiciona, pero su visibilidad es controlada
        self.config_button.grid(row=6, column=0, sticky="ew", padx=10, pady=2)
        
        # CONTROL DE ACCESO: Ocultar Configuración si el rol no es de administrador/gerente
        self._restrict_access()
        
        # --- SECCIÓN: INDICADOR DE TASA DE CAMBIO (Bs/USD) ---
        self.rate_frame = ctk.CTkFrame(self.navigation_frame, fg_color="transparent")
        self.rate_frame.grid(row=7, column=0, sticky="ew", padx=10, pady=(15, 5))
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
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=9, column=0, sticky="ew", padx=10, pady=(10, 20))
        
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

    def _restrict_access(self):
        """Oculta botones sensibles si el usuario no tiene permisos."""
        
        allowed_roles = ["Administrador Total", "Gerente"]
        
        if self.current_user_role not in allowed_roles:
            # Ocultar el botón de Configuración si el rol es, por ejemplo, "Cajero"
            self.config_button.grid_forget()
            
            # Ajustar la posición vertical del marco de la tasa de cambio 
            # para que suba y no quede un espacio vacío.
            self.rate_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=(15, 5))
            
            # Ajustar el peso del grid para que el botón de Cerrar Sesión quede abajo
            self.navigation_frame.grid_rowconfigure(8, weight=1)
            self.navigation_frame.grid_rowconfigure(7, weight=0) # Fila anterior de rate_frame
            self.navigation_frame.grid_rowconfigure(9, weight=0) # Fila anterior de cerrar sesión
            
            # Mover el botón de Cerrar Sesión a la nueva fila 8 (antes 9)
            self.navigation_frame.grid_slaves(row=9)[0].grid(row=8, column=0, sticky="ew", padx=10, pady=(10, 20))


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
            # En caso de error, muestra un mensaje claro
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

        # Buscamos el nombre completo del usuario para una bienvenida personalizada
        user_info = self.db.fetch_one("SELECT nombre_completo FROM usuarios WHERE id = ?", (self.current_user_id,))
        user_name = user_info[0].split()[0] if user_info else "Usuario" # Solo el primer nombre
        
        ctk.CTkLabel(welcome_frame, text=f"Bienvenido(a), {user_name}", 
                     font=ctk.CTkFont(size=30, weight="bold"), text_color=ACCENT_CYAN).grid(row=0, column=0, pady=(100, 5))
        ctk.CTkLabel(welcome_frame, text="Usa el menú lateral para navegar.", 
                     font=ctk.CTkFont(size=16), text_color="gray70").grid(row=1, column=0, pady=(0, 100))
        
        self.pages["home"] = home_frame

        # 2. Páginas funcionales
        self.pages["inventory"] = InventoryPage(self.content_container, self.db, self.current_user_id)
        self.pages["pos"] = PosPage(self.content_container, self.db, self.current_user_id)
        
        # IMPORTANTE: Pasamos el método de actualización y el rol del usuario a ConfigPage
        self.pages["config"] = ConfigPage(
            self.content_container, 
            self.db, 
            self.current_user_id, 
            self.update_exchange_rate_label, 
            self.current_user_role
        )


    def select_frame_by_name(self, name):
        """Muestra la página seleccionada y oculta las demás."""
        
        # Control de acceso antes de intentar cargar la página
        if name == "config" and self.current_user_role not in ["Administrador Total", "Gerente"]:
            messagebox.showwarning("Acceso Denegado", "No tiene permisos para acceder a Configuración.")
            return

        # Desactivar color de todos los botones
        self.home_button.configure(fg_color="transparent")
        self.inventory_button.configure(fg_color="transparent")
        self.pos_button.configure(fg_color="transparent")
        self.config_button.configure(fg_color="transparent")

        for page_name, page_frame in self.pages.items():
            if page_name == name:
                
                current_rate = self.update_exchange_rate_label() 
                
                # Si es Inventario, llamar a load_products para recargar datos
                if page_name == "inventory":
                    try:
                        page_frame.load_products(current_rate)
                    except AttributeError:
                        pass
                
                # Si es POS, actualizar la tasa localmente
                elif page_name == "pos":
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
