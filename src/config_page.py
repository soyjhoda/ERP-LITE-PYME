import customtkinter as ctk
from tkinter import messagebox, ttk
from .utils import is_valid_float

# Definiciones de estilo
ACCENT_CYAN = "#00FFFF"      
ACCENT_GREEN = "#00c853"
ACCENT_RED = "#c0392b"
BACKGROUND_DARK = "#0D1B2A"  
FRAME_MID = "#1B263B"
FRAME_LIGHT = "#2c3e50"

class ConfigPage(ctk.CTkFrame):
    """Panel de Administración centralizado para tareas sensibles (Tasa, Usuarios, Seguridad)."""
    
    # CONSTRUCTOR ACTUALIZADO: Acepta y guarda el rol del usuario
    def __init__(self, master, db_manager, user_id, update_rate_callback, user_role): 
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.user_id = user_id
        self.user_role = user_role # ¡Nuevo! Rol del usuario actual
        self.update_rate_callback = update_rate_callback 
        
        self.grid_rowconfigure(0, weight=1) # El TabView ocupa todo el espacio
        self.grid_columnconfigure(0, weight=1)

        self._create_widgets()
        self.load_current_rate()

    def _create_widgets(self):
        """Crea todos los elementos de la UI, organizados por pestañas."""
        
        # Título principal de la página
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        title_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(title_frame, text="🛡️ PANEL DE ADMINISTRACIÓN", 
                     font=ctk.CTkFont(size=26, weight="bold"), 
                     text_color=ACCENT_CYAN).grid(row=0, column=0, sticky="w", pady=(0, 10))

        # --- TabView para organizar secciones ---
        self.tabview = ctk.CTkTabview(self, fg_color=BACKGROUND_DARK, segmented_button_fg_color=FRAME_MID)
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        # --- Pestaña 1: Configuración de Empresa (Tasa de Cambio) ---
        self.tabview.add("Empresa y Finanzas")
        self._setup_empresa_tab(self.tabview.tab("Empresa y Finanzas"))
        
        # --- Pestaña 2: Gestión de Usuarios (Restringida) ---
        # Solo añadimos la pestaña de usuarios si el rol es Administrador Total
        if self.user_role == "Administrador Total":
            self.tabview.add("Gestión de Usuarios")
            self._setup_users_tab(self.tabview.tab("Gestión de Usuarios"))
        else:
             # Opcional: mostrar un mensaje de acceso denegado en el log
             print(f"Usuario {self.user_role} no tiene acceso a la gestión de usuarios.")
        
        # --- Pestaña 3: Herramientas y Seguridad ---
        self.tabview.add("Herramientas y Seguridad")
        self._setup_security_tab(self.tabview.tab("Herramientas y Seguridad"))
        
        # Establecer la pestaña inicial
        self.tabview.set("Empresa y Finanzas")

    # =======================================================================
    # FUNCIONES DE SETUP DE PESTAÑAS
    # =======================================================================

    def _setup_empresa_tab(self, tab_frame):
        """Configura la pestaña de Tasa de Cambio."""
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_rowconfigure(0, weight=0) # Fila de la tarjeta de tasa
        tab_frame.grid_rowconfigure(1, weight=1) # Espacio libre

        # Tarjeta de Tasa de Cambio (MOVIMIENTO DE CÓDIGO ANTERIOR)
        rate_card = ctk.CTkFrame(tab_frame, fg_color=FRAME_MID, corner_radius=10)
        rate_card.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        rate_card.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(rate_card, text="Tasa de Cambio Actual (Bs/USD)", 
                     font=ctk.CTkFont(size=18, weight="bold"), 
                     text_color="white").grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 5))
        
        # Valor Actual
        ctk.CTkLabel(rate_card, text="Valor Actual:", text_color="gray70").grid(row=1, column=0, sticky="w", padx=20, pady=(10, 0))
        self.current_rate_label = ctk.CTkLabel(rate_card, text="Cargando...", 
                                               font=ctk.CTkFont(size=22, weight="bold"), 
                                               text_color=ACCENT_GREEN)
        self.current_rate_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 20))
        
        # Establecer Nueva Tasa
        ctk.CTkLabel(rate_card, text="Establecer Nueva Tasa:", text_color="gray70").grid(row=1, column=1, sticky="w", padx=20, pady=(10, 0))
        self.new_rate_entry = ctk.CTkEntry(rate_card, placeholder_text="Ej: 36.50", width=150, font=ctk.CTkFont(size=16))
        self.new_rate_entry.grid(row=2, column=1, sticky="w", padx=20, pady=(0, 20))
        
        # Botón para guardar
        save_button = ctk.CTkButton(rate_card, text="💾 Guardar Tasa", 
                                    command=self.save_exchange_rate, 
                                    fg_color=ACCENT_CYAN, 
                                    text_color=BACKGROUND_DARK,
                                    hover_color=ACCENT_CYAN.lower().replace('f', 'e'))
        save_button.grid(row=3, column=0, columnspan=2, pady=(0, 20))

    def _setup_users_tab(self, tab_frame):
        """Configura la pestaña de Gestión de Usuarios (Añadir, Editar Rol, Eliminar)."""
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(tab_frame, text="👩‍💻 GESTIÓN DE CUENTAS DE USUARIO", 
                     font=ctk.CTkFont(size=20, weight="bold"), 
                     text_color="white").grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Placeholder temporal
        placeholder = ctk.CTkFrame(tab_frame, fg_color=FRAME_LIGHT, corner_radius=10)
        placeholder.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        placeholder.grid_columnconfigure(0, weight=1)
        placeholder.grid_rowconfigure(0, weight=1)
        
        ctk.CTkLabel(placeholder, text="[ÁREA DE TRABAJO EN LA FASE 4]", 
                     font=ctk.CTkFont(size=18), text_color="gray50").grid(row=0, column=0)
        
    def _setup_security_tab(self, tab_frame):
        """Configura la pestaña de Herramientas y Seguridad (Backup, Info)."""
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(tab_frame, text="🔑 HERRAMIENTAS Y COPIA DE SEGURIDAD", 
                     font=ctk.CTkFont(size=20, weight="bold"), 
                     text_color="white").grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Tarjeta de Backup
        backup_card = ctk.CTkFrame(tab_frame, fg_color=FRAME_MID, corner_radius=10)
        backup_card.grid(row=1, column=0, sticky="nw", padx=20, pady=(10, 20))
        backup_card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(backup_card, text="Copia de Seguridad (Backup)", 
                     font=ctk.CTkFont(size=16, weight="bold"), 
                     text_color="white").grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(backup_card, text="Guarda una copia de seguridad de la base de datos (profitus.db).", 
                     text_color="gray70").grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))
        
        ctk.CTkButton(backup_card, text="⬇️ Generar Backup", command=self.create_backup, 
                      fg_color=ACCENT_GREEN, hover_color="#008a38",
                      font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, padx=20, pady=(5, 20), sticky="w")


    # =======================================================================
    # LÓGICA DE FUNCIONALIDADES
    # =======================================================================
    
    def load_current_rate(self):
        """Carga la tasa de cambio actual desde la DB y actualiza el label local."""
        try:
            rate = self.db.get_exchange_rate()
            if rate is not None:
                self.current_rate_label.configure(text=f"Bs. {rate:,.2f}", text_color=ACCENT_GREEN)
            else:
                self.current_rate_label.configure(text="No definida", text_color=ACCENT_RED)
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudo cargar la tasa de cambio: {e}")
            self.current_rate_label.configure(text="Error", text_color=ACCENT_RED)

    def save_exchange_rate(self):
        """Guarda la nueva tasa de cambio y actualiza el dashboard."""
        
        # Restricción de permiso de escritura (Administrador Total y Gerente pueden cambiar la tasa)
        if self.user_role not in ["Administrador Total", "Gerente"]:
            messagebox.showwarning("Permiso Denegado", "Solo Administradores y Gerentes pueden modificar la tasa de cambio.")
            return

        new_rate_str = self.new_rate_entry.get().strip()
        
        if not new_rate_str:
            messagebox.showwarning("Advertencia", "Por favor, introduce un valor para la nueva tasa.")
            return
        
        if not is_valid_float(new_rate_str):
            messagebox.showerror("Error de Formato", "El valor introducido no es un número decimal válido.")
            return

        try:
            new_rate_float = float(new_rate_str)
            if new_rate_float <= 0:
                 messagebox.showerror("Error de Valor", "La tasa de cambio debe ser mayor a cero.")
                 return

            # 1. Guardar en la base de datos
            self.db.set_exchange_rate(new_rate_float)
            
            # 2. Actualizar el label local en esta página
            self.current_rate_label.configure(text=f"Bs. {new_rate_float:,.2f}", text_color=ACCENT_GREEN)
            
            # 3. Llamar al callback para actualizar el dashboard (menú lateral)
            self.update_rate_callback()
            
            self.new_rate_entry.delete(0, 'end')
            messagebox.showinfo("Éxito", f"Tasa de cambio actualizada a Bs. {new_rate_float:,.2f}.")

        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Ocurrió un error al guardar la tasa: {e}")

    def create_backup(self):
        """Inicia el proceso de creación de la copia de seguridad de la base de datos."""
        # Restricción: Solo Administradores pueden hacer backup
        if self.user_role != "Administrador Total":
            messagebox.showwarning("Permiso Denegado", "Solo el Administrador Total puede crear copias de seguridad.")
            return
        
        try:
            # Llama a la función de la DB Manager para realizar el backup
            backup_path = self.db.create_backup()
            messagebox.showinfo("Backup Creado", 
                                f"Copia de seguridad de la base de datos creada exitosamente.\n\n"
                                f"Ruta: {backup_path}")
        except Exception as e:
            messagebox.showerror("Error de Backup", f"No se pudo crear la copia de seguridad: {e}")
