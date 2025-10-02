import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
from .utils import is_valid_float
import hashlib 

# Definiciones de estilo
ACCENT_CYAN = "#00FFFF"
ACCENT_GREEN = "#00c853"
ACCENT_RED = "#c0392b"
BACKGROUND_DARK = "#0D1B2A"
FRAME_MID = "#1B263B"
FRAME_LIGHT = "#2c3e50"

# =======================================================================
# VENTANA MODAL PARA CREAR USUARIO (Mantenida)
# =======================================================================

class CreateUserWindow(ctk.CTkToplevel):
    def __init__(self, master, users_data, refresh_callback):
        super().__init__(master)
        self.master = master
        self.users_data = users_data
        self.refresh_callback = refresh_callback
        
        self.title("Crear Nuevo Usuario")
        self.geometry("400x480")
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        
        self._create_widgets()

    def _create_widgets(self):
        # Título
        ctk.CTkLabel(self, text="Registro de Nuevo Usuario", font=ctk.CTkFont(size=20, weight="bold"), 
                     text_color=ACCENT_CYAN).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="n")

        # Contenedor para campos
        form_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)
        
        # 1. Nombre Completo
        ctk.CTkLabel(form_frame, text="Nombre Completo:", text_color="gray70").grid(row=0, column=0, sticky="w", padx=15, pady=(15, 0))
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: Ana López", font=ctk.CTkFont(size=14))
        self.name_entry.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        # 2. Nombre de Usuario (Login)
        ctk.CTkLabel(form_frame, text="Nombre de Usuario (Login):", text_color="gray70").grid(row=2, column=0, sticky="w", padx=15, pady=(10, 0))
        self.username_entry = ctk.CTkEntry(form_frame, placeholder_text="Ej: ana.lopez", font=ctk.CTkFont(size=14))
        self.username_entry.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 10))

        # 3. Contraseña
        ctk.CTkLabel(form_frame, text="Contraseña Inicial:", text_color="gray70").grid(row=4, column=0, sticky="w", padx=15, pady=(10, 0))
        self.password_entry = ctk.CTkEntry(form_frame, placeholder_text="Mínimo 6 caracteres", show="*", font=ctk.CTkFont(size=14))
        self.password_entry.grid(row=5, column=0, sticky="ew", padx=15, pady=(0, 10))

        # 4. Rol
        ctk.CTkLabel(form_frame, text="Rol Asignado:", text_color="gray70").grid(row=6, column=0, sticky="w", padx=15, pady=(10, 0))
        self.role_combobox = ctk.CTkComboBox(form_frame, 
                                             values=["Vendedor", "Gerente", "Administrador Total"],
                                             state="readonly")
        self.role_combobox.set("Vendedor")
        self.role_combobox.grid(row=7, column=0, sticky="ew", padx=15, pady=(0, 15))
        
        # 5. Botón de Creación
        ctk.CTkButton(self, text="✅ Registrar Usuario", command=self._create_user_action, 
                      fg_color=ACCENT_CYAN, text_color=BACKGROUND_DARK, hover_color="#00bebe",
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))


    def _create_user_action(self):
        """Valida y añade el nuevo usuario a la simulación."""
        name = self.name_entry.get().strip()
        username = self.username_entry.get().strip().lower() # Usar minúsculas para consistencia
        password = self.password_entry.get()
        role = self.role_combobox.get()
        
        if not all([name, username, password, role]):
            messagebox.showwarning("Faltan Datos", "Todos los campos (excepto foto) son obligatorios.")
            return
        
        if len(password) < 6:
            messagebox.showwarning("Contraseña Débil", "La contraseña debe tener al menos 6 caracteres.")
            return

        # SIMULACIÓN DE VALIDACIÓN DE USERNAME ÚNICO
        if username in self.users_data.keys():
             messagebox.showerror("Error", "El nombre de usuario (login) ya existe. Elija otro.")
             return
        
        # Generar un ID (Usamos el username como ID/Key en la simulación para mayor consistencia)
        # NOTA: En la DB real, el ID es INTEGER AUTOINCREMENT. Aquí usamos el username temporalmente.
        new_user_id = username 
        
        # Generar hash de la contraseña (simulación)
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Estructura de datos completa 
        new_user_data = {
            "name": name,
            "role": role,
            "username": username, 
            "password_hash": hashed_password,
            "photo_path": None # Inicialmente sin foto
        }
        
        # Añadir a la simulación local
        self.users_data[new_user_id] = new_user_data
        
        # Lógica DB: self.master.db.create_user(username, password, name, role) 

        # Actualizar el Treeview principal y cerrar
        self.refresh_callback(self.users_data)
        messagebox.showinfo("Éxito", f"Usuario '{name}' creado exitosamente.\nNombre de usuario (login): {username}")
        self.destroy()

# =======================================================================
# NUEVA VENTANA MODAL PARA CAMBIAR CONTRASEÑA
# =======================================================================

class ChangePasswordWindow(ctk.CTkToplevel):
    def __init__(self, master, db_manager, user_id_to_edit, username_to_edit):
        super().__init__(master)
        self.db = db_manager
        self.user_id = user_id_to_edit # ID del usuario en la DB (clave para el UPDATE)
        self.username = username_to_edit
        
        self.title(f"Cambiar Contraseña: {self.username}")
        self.geometry("350x300")
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        self._create_widgets()

    def _create_widgets(self):
        # Título
        ctk.CTkLabel(self, text="🔑 Nueva Contraseña", font=ctk.CTkFont(size=20, weight="bold"), 
                     text_color=ACCENT_CYAN).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="n")

        # Contenedor para campos
        form_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)
        
        # 1. Nueva Contraseña
        ctk.CTkLabel(form_frame, text="Nueva Contraseña:", text_color="gray70").grid(row=0, column=0, sticky="w", padx=15, pady=(15, 0))
        self.new_password_entry = ctk.CTkEntry(form_frame, placeholder_text="Mínimo 6 caracteres", show="*", font=ctk.CTkFont(size=14))
        self.new_password_entry.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))

        # 2. Confirmar Contraseña
        ctk.CTkLabel(form_frame, text="Confirmar Contraseña:", text_color="gray70").grid(row=2, column=0, sticky="w", padx=15, pady=(10, 0))
        self.confirm_password_entry = ctk.CTkEntry(form_frame, placeholder_text="Repita la contraseña", show="*", font=ctk.CTkFont(size=14))
        self.confirm_password_entry.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 15))
        
        # 3. Botón de Actualizar
        ctk.CTkButton(self, text="✅ Actualizar Contraseña", command=self._change_password_action, 
                      fg_color=ACCENT_GREEN, text_color=BACKGROUND_DARK, hover_color="#008a38",
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))

    def _change_password_action(self):
        """Valida y actualiza la contraseña del usuario en la base de datos."""
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not new_password or not confirm_password:
            messagebox.showwarning("Faltan Datos", "Debe completar ambos campos de contraseña.")
            return

        if len(new_password) < 6:
            messagebox.showwarning("Contraseña Débil", "La contraseña debe tener al menos 6 caracteres.")
            return
            
        if new_password != confirm_password:
            messagebox.showerror("Error", "Las contraseñas no coinciden.")
            return

        try:
            # LLAMADA AL DB_MANAGER REAL
            # Esta función hashea la contraseña internamente antes de guardarla.
            success = self.db.update_user_password(self.user_id, new_password)
            
            if success:
                # SIMULACIÓN DE ACTUALIZACIÓN LOCAL (Para consistencia en la vista)
                # NOTA: En la simulación anterior usábamos el diccionario users_data del master.
                # Aquí no es necesario actualizar la UI principal, solo el hash en la "DB" (db_manager).
                
                messagebox.showinfo("Éxito", f"Contraseña de '{self.username}' actualizada exitosamente.")
                self.destroy()
            else:
                messagebox.showerror("Error", "No se pudo actualizar la contraseña. Verifique la conexión a la base de datos.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado al actualizar la contraseña: {e}")

# =======================================================================
# VENTANA MODAL PARA EDITAR USUARIO [NUEVO]
# =======================================================================

class EditUserWindow(ctk.CTkToplevel):
    def __init__(self, master, db_manager, user_id_to_edit, refresh_callback):
        super().__init__(master)
        self.master = master
        self.db = db_manager # Manager de DB para llamadas reales
        self.user_id_to_edit = user_id_to_edit
        self.refresh_callback = refresh_callback
        
        self.user_data = self._load_user_data() # Cargar datos iniciales
        
        if not self.user_data:
            messagebox.showerror("Error", f"No se pudo cargar el usuario con ID: {user_id_to_edit}")
            self.destroy()
            return
            
        self.title(f"Editar Usuario: {self.user_data.get('name', 'N/A')}")
        self.geometry("400x520")
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        
        self.grid_columnconfigure(0, weight=1)
        self._create_widgets()

    def _load_user_data(self):
        """Intenta cargar los datos del usuario usando el db_manager."""
        # SIMULACIÓN (Usando el diccionario local de ConfigPage)
        return self.master.users_data.get(self.user_id_to_edit) 
        # return self.db.get_user_by_id(self.user_id_to_edit) # Línea a usar con la DB real

    def _create_widgets(self):
        # Título
        ctk.CTkLabel(self, text="🛠️ Editar Datos de Usuario", font=ctk.CTkFont(size=20, weight="bold"), 
                     text_color=ACCENT_CYAN).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="n")

        # Contenedor para campos
        form_frame = ctk.CTkFrame(self, fg_color=FRAME_MID, corner_radius=10)
        form_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        form_frame.grid_columnconfigure(0, weight=1)
        
        # ID de Usuario (Solo lectura)
        ctk.CTkLabel(form_frame, text=f"ID (Login): {self.user_data['username']}", text_color="gray50").grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))
        
        # 1. Nombre Completo
        ctk.CTkLabel(form_frame, text="Nombre Completo:", text_color="gray70").grid(row=1, column=0, sticky="w", padx=15, pady=(10, 0))
        self.name_entry = ctk.CTkEntry(form_frame, font=ctk.CTkFont(size=14))
        self.name_entry.insert(0, self.user_data.get("name", ""))
        self.name_entry.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 10))

        # 2. Rol
        ctk.CTkLabel(form_frame, text="Rol Asignado:", text_color="gray70").grid(row=3, column=0, sticky="w", padx=15, pady=(10, 0))
        self.role_combobox = ctk.CTkComboBox(form_frame, 
                                             values=["Vendedor", "Gerente", "Administrador Total"],
                                             state="readonly")
        self.role_combobox.set(self.user_data.get("role", "Vendedor"))
        self.role_combobox.grid(row=4, column=0, sticky="ew", padx=15, pady=(0, 20))
        
        # 3. Botón para Guardar Cambios
        ctk.CTkButton(form_frame, text="💾 Guardar Cambios", command=self._update_user_action, 
                      fg_color=ACCENT_GREEN, hover_color="#008a38",
                      font=ctk.CTkFont(size=16, weight="bold")).grid(row=5, column=0, sticky="ew", padx=15, pady=(10, 10))
                      
        # 4. Botón para Cambiar Contraseña (Separado por seguridad)
        ctk.CTkButton(form_frame, text="🔑 Cambiar Contraseña", command=self._open_password_change, 
                      fg_color=FRAME_LIGHT, hover_color=FRAME_MID, border_color=ACCENT_CYAN, border_width=2,
                      font=ctk.CTkFont(size=14)).grid(row=6, column=0, sticky="ew", padx=15, pady=(0, 20))


    def _update_user_action(self):
        """Valida y actualiza el usuario usando db_manager.update_user_details."""
        new_name = self.name_entry.get().strip()
        new_role = self.role_combobox.get()
        user_id_key = self.user_id_to_edit # El ID/Key usado en la simulación
        
        if not all([new_name, new_role]):
            messagebox.showwarning("Faltan Datos", "El nombre y el rol son obligatorios.")
            return

        # LLAMADA A LA FUNCIÓN DE LA BASE DE DATOS
        # Aquí se debería llamar a db_manager.update_user_details
        # Se asume que el user_id_to_edit es el ID numérico de la DB, 
        # aunque en el mock es el username. Usaremos el username (key) como referencia.
        
        # Simulación:
        self.master.users_data[user_id_key]['name'] = new_name
        self.master.users_data[user_id_key]['role'] = new_role
        
        # Lógica DB: self.db.update_user_details(self.user_id_to_edit, ..., new_name, new_role, ...)

        messagebox.showinfo("Éxito", f"Datos del usuario '{new_name}' actualizados.")
        self.refresh_callback(self.master.users_data)
        self.destroy()

    def _open_password_change(self):
        """Abre la ventana modal para solicitar y confirmar una nueva contraseña."""
        # Abrir la nueva ventana modal
        ChangePasswordWindow(
            self.master, 
            self.db, 
            self.user_id_to_edit, # ID del usuario a editar
            self.user_data.get('username') # Username para mostrar en el título
        )


# =======================================================================
# CLASE PRINCIPAL: CONFIG PAGE
# =======================================================================

class ConfigPage(ctk.CTkFrame):
    """Panel de Administración centralizado para tareas sensibles (Tasa, Usuarios, Seguridad)."""
    
    def __init__(self, master, db_manager, user_id, update_rate_callback, user_role):
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.user_id = user_id
        self.user_role = user_role # Rol del usuario actual
        self.update_rate_callback = update_rate_callback
        
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Estado para la gestión de usuarios
        self.current_selected_user_id = None
        self.users_data = {} # Almacenará los datos de usuarios (simulados o reales)
        
        # Referencias de botones y labels para control de estado (mejora de UX)
        self.delete_user_button = None
        self.save_role_button = None
        self.edit_full_user_button = None 

        # Referencias para el control panel de edición
        self.edit_user_name_label = None 
        self.edit_username_label = None


        self._configure_ttk_style()
        self._create_widgets()
        self.load_current_rate()
    
    def _configure_ttk_style(self):
        """Configuración de estilo para el Treeview (ttk)."""
        style = ttk.Style()
        style.theme_use("clam") # 'clam' theme works well with dark customtkinter
        style.configure("Treeview", 
                        background=FRAME_MID, 
                        foreground="white",
                        fieldbackground=FRAME_MID,
                        bordercolor=FRAME_MID,
                        rowheight=28)
        style.configure("Treeview.Heading", 
                        font=('CTkDefaultFont', 11, 'bold'),
                        background=FRAME_MID,
                        foreground=ACCENT_CYAN)
        style.map('Treeview', background=[('selected', ACCENT_CYAN)])

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
        if self.user_role == "Administrador Total":
            self.tabview.add("Gestión de Usuarios")
            self._setup_users_tab(self.tabview.tab("Gestión de Usuarios"))
            self.load_users_data() # Cargar datos iniciales/reales de usuarios
        else:
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
        tab_frame.grid_rowconfigure(0, weight=0)
        tab_frame.grid_rowconfigure(1, weight=1)

        # Tarjeta de Tasa de Cambio
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
                                             hover_color="#00bebe")
        save_button.grid(row=3, column=0, columnspan=2, pady=(0, 20))

    def _setup_users_tab(self, tab_frame):
        """Configura la pestaña de Gestión de Usuarios."""
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_rowconfigure(1, weight=1)

        # Título
        ctk.CTkLabel(tab_frame, text="👩‍💻 GESTIÓN DE CUENTAS DE USUARIO", 
                                     font=ctk.CTkFont(size=20, weight="bold"), 
                                     text_color="white").grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # Contenedor principal para la gestión
        main_container = ctk.CTkFrame(tab_frame, fg_color=FRAME_LIGHT, corner_radius=10)
        main_container.grid(row=1, column=0, sticky="nsew", padx=20, pady=(10, 20))
        main_container.grid_columnconfigure(0, weight=3) # Lista de usuarios
        main_container.grid_columnconfigure(1, weight=1) # Controles de edición
        main_container.grid_rowconfigure(0, weight=1)

        # --- Sub-sección Izquierda: Listado de Usuarios (Treeview) ---
        list_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(15, 5), pady=15)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(list_frame, text="Usuarios Registrados (Click para editar)", 
                                     font=ctk.CTkFont(size=16, weight="bold"), 
                                     text_color=ACCENT_CYAN).grid(row=0, column=0, sticky="w", pady=(0, 5))

        # Treeview
        self.users_tree = ttk.Treeview(list_frame, columns=("ID", "Nombre", "Rol"), show="headings")
        self.users_tree.heading("ID", text="ID (Corto)", anchor=ctk.W)
        self.users_tree.heading("Nombre", text="Nombre de Usuario", anchor=ctk.W)
        self.users_tree.heading("Rol", text="Rol Actual", anchor=ctk.W)
        
        self.users_tree.column("ID", width=80, stretch=ctk.NO, anchor=ctk.W)
        self.users_tree.column("Nombre", minwidth=150, anchor=ctk.W)
        self.users_tree.column("Rol", width=120, stretch=ctk.NO, anchor=ctk.W)

        self.users_tree.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        # Scrollbar vertical
        tree_scrollbar = ctk.CTkScrollbar(list_frame, command=self.users_tree.yview)
        tree_scrollbar.grid(row=1, column=1, sticky="ns")
        self.users_tree.configure(yscrollcommand=tree_scrollbar.set)
        
        # Bind the selection event (for editing)
        self.users_tree.bind("<<TreeviewSelect>>", self._on_user_select)
        
        # NUEVO BOTÓN: Crear Usuario (Row 2)
        create_user_button = ctk.CTkButton(list_frame, text="➕ Crear Nuevo Usuario", 
                                             command=self._open_create_user_window, 
                                             fg_color=ACCENT_GREEN, hover_color="#008a38",
                                             font=ctk.CTkFont(size=14, weight="bold"))
        create_user_button.grid(row=2, column=0, sticky="ew", pady=(5, 10))

        # --- Sub-sección Derecha: Controles de Edición ---
        control_frame = ctk.CTkFrame(main_container, fg_color=FRAME_MID, corner_radius=8)
        control_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        control_frame.grid_columnconfigure(0, weight=1)
        
        # Título del panel de control
        ctk.CTkLabel(control_frame, text="Control Rápido de Rol", 
                                     font=ctk.CTkFont(size=16, weight="bold"), 
                                     text_color="white").grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # ID (solo lectura)
        ctk.CTkLabel(control_frame, text="ID de Usuario (Corto):", text_color="gray70").grid(row=1, column=0, sticky="w", padx=15, pady=(10, 0))
        self.edit_user_id = ctk.CTkLabel(control_frame, text="Seleccione un usuario", text_color="gray50")
        self.edit_user_id.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 10))
        
        # Nombre (solo lectura)
        ctk.CTkLabel(control_frame, text="Nombre Completo:", text_color="gray70").grid(row=3, column=0, sticky="w", padx=15, pady=(10, 0))
        self.edit_user_name_label = ctk.CTkLabel(control_frame, text="", text_color="white") # Referencia renombrada
        self.edit_user_name_label.grid(row=4, column=0, sticky="w", padx=15, pady=(0, 10))

        # Username (Login) - NUEVO
        ctk.CTkLabel(control_frame, text="Username (Login):", text_color="gray70").grid(row=5, column=0, sticky="w", padx=15, pady=(10, 0))
        self.edit_username_label = ctk.CTkLabel(control_frame, text="", text_color="white") # Nueva referencia
        self.edit_username_label.grid(row=6, column=0, sticky="w", padx=15, pady=(0, 10))

        # Rol
        ctk.CTkLabel(control_frame, text="Nuevo Rol:", text_color="gray70").grid(row=7, column=0, sticky="w", padx=15, pady=(10, 0))
        self.role_combobox = ctk.CTkComboBox(control_frame, 
                                             values=["Vendedor", "Gerente", "Administrador Total"],
                                             state="readonly")
        self.role_combobox.set("Vendedor")
        self.role_combobox.grid(row=8, column=0, sticky="ew", padx=15, pady=(0, 20))

        # Botón de Guardar Rol Rápido
        self.save_role_button = ctk.CTkButton(control_frame, text="Guardar Rol", command=self.save_user_role,
                             fg_color=ACCENT_GREEN, hover_color="#008a38")
        self.save_role_button.grid(row=9, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        # Botón de Edición Completa [NUEVO]
        self.edit_full_user_button = ctk.CTkButton(control_frame, text="✏️ Editar Usuario Completo", 
                                                     command=self._open_edit_user_window,
                                                     fg_color=ACCENT_CYAN, text_color=BACKGROUND_DARK, hover_color="#00bebe")
        self.edit_full_user_button.grid(row=10, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        # Botón de Eliminar (Referencia guardada para control de estado)
        self.delete_user_button = ctk.CTkButton(control_frame, text="Eliminar Usuario 🗑️", command=self.delete_user, 
                             fg_color=ACCENT_RED, hover_color="#8b0000")
        self.delete_user_button.grid(row=11, column=0, sticky="ew", padx=15, pady=(0, 15))


    def _setup_security_tab(self, tab_frame):
        """Configura la pestaña de Herramientas y Seguridad (Backup, Info)."""
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(tab_frame, text="🔑 HERRAMIENTAS Y COPIA DE SEGURIDAD", 
                                     font=ctk.CTkFont(size=20, weight="bold"), 
                                     text_color="white").grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

        # --- TARJETA DE BACKUP (Exportar) ---
        backup_card = ctk.CTkFrame(tab_frame, fg_color=FRAME_MID, corner_radius=10)
        backup_card.grid(row=1, column=0, sticky="ew", padx=20, pady=(10, 5))
        backup_card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(backup_card, text="Copia de Seguridad (Exportar)", 
                                     font=ctk.CTkFont(size=16, weight="bold"), 
                                     text_color="white").grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(backup_card, text="Guarda una copia de seguridad de la base de datos (profitus.db) en una ruta externa.", 
                                     text_color="gray70").grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))
        
        ctk.CTkButton(backup_card, text="⬇️ Generar Backup", command=self.create_backup, 
                                             fg_color=ACCENT_GREEN, hover_color="#008a38",
                                             font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, padx=20, pady=(5, 20), sticky="w")
                                             
        # --- TARJETA DE RESTAURACIÓN (Importar) ---
        restore_card = ctk.CTkFrame(tab_frame, fg_color=FRAME_MID, corner_radius=10)
        restore_card.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 20))
        restore_card.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(restore_card, text="Restaurar Base de Datos (Importar)", 
                                     font=ctk.CTkFont(size=16, weight="bold"), 
                                     text_color="white").grid(row=0, column=0, sticky="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(restore_card, text="🚨 ¡PELIGRO! Reemplaza la DB actual (profitus.db) con un archivo de backup. REQUIERE REINICIO.", 
                                     text_color=ACCENT_RED).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))
        
        ctk.CTkButton(restore_card, text="⬆️ Restaurar desde Backup", command=self.restore_database, 
                                             fg_color=ACCENT_RED, hover_color="#8b0000",
                                             font=ctk.CTkFont(size=14, weight="bold")).grid(row=2, column=0, padx=20, pady=(5, 20), sticky="w")


    # =======================================================================
    # LÓGICA DE FUNCIONALIDADES - TASA DE CAMBIO 
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
        
        if self.user_role not in ["Administrador Total", "Gerente"]:
            messagebox.showwarning("Permiso Denegado", "Solo Administradores y Gerentes pueden modificar la tasa de cambio.")
            return

        new_rate_str = self.new_rate_entry.get().strip()
        
        if not new_rate_str:
            messagebox.showwarning("Advertencia", "Por favor, introduce un valor para la nueva tasa.")
            return
        
        # is_valid_float comes from .utils
        if not is_valid_float(new_rate_str): 
            messagebox.showerror("Error de Formato", "El valor introducido no es un número decimal válido.")
            return

        try:
            new_rate_float = float(new_rate_str)
            if new_rate_float <= 0:
                messagebox.showerror("Error de Valor", "La tasa de cambio debe ser mayor a cero.")
                return

            self.db.set_exchange_rate(new_rate_float)
            
            self.current_rate_label.configure(text=f"Bs. {new_rate_float:,.2f}", text_color=ACCENT_GREEN)
            
            # Notifica al callback principal para actualizar el valor en el menú lateral.
            self.update_rate_callback() 
            
            self.new_rate_entry.delete(0, 'end')
            messagebox.showinfo("Éxito", f"Tasa de cambio actualizada a Bs. {new_rate_float:,.2f}.")

        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Ocurrió un error al guardar la tasa: {e}")
            
    # =======================================================================
    # LÓGICA DE FUNCIONALIDADES - BACKUP Y RESTAURACIÓN 
    # =======================================================================

    def create_backup(self):
        """Inicia el proceso de creación de la copia de seguridad."""
        if self.user_role != "Administrador Total":
            messagebox.showwarning("Permiso Denegado", "Solo el Administrador Total puede crear copias de seguridad.")
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"profitus_backup_{timestamp}.db"
            
            destination_path = filedialog.asksaveasfilename(
                defaultextension=".db",
                initialfile=default_filename,
                title="Guardar Copia de Seguridad de la Base de Datos",
                filetypes=[("Archivos de Base de Datos SQLite", "*.db"), ("Todos los archivos", "*.*")]
            )
            
            if not destination_path:
                messagebox.showinfo("Cancelado", "El proceso de copia de seguridad fue cancelado.")
                return
                
            success, message = self.db.perform_backup(destination_path)
            
            if success:
                messagebox.showinfo("Backup Creado", 
                                     f"Copia de seguridad de la base de datos creada exitosamente.\n\n"
                                     f"Ruta: {destination_path}")
            else:
                messagebox.showerror("Error de Backup", f"No se pudo crear la copia de seguridad:\n{message}")
                
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error inesperado durante el backup: {e}")

    def restore_database(self):
        """Inicia el proceso de restauración de la base de datos desde un archivo de backup."""
        if self.user_role != "Administrador Total":
            messagebox.showwarning("Permiso Denegado", "Solo el Administrador Total puede restaurar la base de datos.")
            return

        if not messagebox.askyesno("Confirmar Restauración (Peligro)", 
                                     "🚨 ¡ADVERTENCIA! Este proceso **REEMPLAZARÁ PERMANENTEMENTE** la base de datos actual.\n"
                                     "Cualquier dato añadido desde el último backup se perderá.\n\n"
                                     "¿Está SEGURO que desea continuar con la restauración?"):
            return 
        
        try:
            source_path = filedialog.askopenfilename(
                title="Seleccionar Archivo de Base de Datos para Restaurar",
                filetypes=[("Archivos de Base de Datos SQLite", "*.db")]
            )
            
            if not source_path:
                messagebox.showinfo("Cancelado", "El proceso de restauración fue cancelado.")
                return
                
            success, message = self.db.restore_backup(source_path)
            
            if success:
                messagebox.showinfo("Restauración Exitosa", 
                                     f"{message}\n\n"
                                     "***La aplicación DEBE REINICIARSE para cargar los datos restaurados.***")
            else:
                messagebox.showerror("Error de Restauración", f"No se pudo restaurar la base de datos:\n{message}")
                
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error inesperado durante la restauración: {e}")

    # =======================================================================
    # LÓGICA DE FUNCIONALIDADES - GESTIÓN DE USUARIOS
    # =======================================================================
    
    def _open_create_user_window(self):
        """Abre la ventana modal para crear un nuevo usuario."""
        if self.user_role != "Administrador Total":
            messagebox.showwarning("Permiso Denegado", "Solo el Administrador Total puede crear usuarios.")
            return
        
        # Pasa la referencia al método que actualizará la lista
        CreateUserWindow(self, self.users_data, self._refresh_user_tree)
    
    def _open_edit_user_window(self):
        """Abre la ventana modal para editar el usuario seleccionado."""
        if not self.current_selected_user_id:
            messagebox.showwarning("Advertencia", "Debe seleccionar un usuario para editar.")
            return
            
        if self.user_role != "Administrador Total":
            messagebox.showwarning("Permiso Denegado", "Solo el Administrador Total puede editar usuarios.")
            return
            
        # Pasa el ID del usuario seleccionado, el db_manager y el callback de refresco
        EditUserWindow(self, self.db, self.current_selected_user_id, self._refresh_user_tree)

    def _get_mock_users(self):
        """Simula la obtención de usuarios. Reemplazar con self.db.get_all_users()"""
        # (Lógica de mock mantenida exactamente igual para asegurar la simulación)
        user_id_str = str(self.user_id) 
        
        def mock_hash(password_prefix):
            return hashlib.sha256(f"pass_{password_prefix}".encode()).hexdigest()
        
        mock_users = {
            user_id_str: {
                "name": "Admin Logueado", 
                "role": self.user_role, 
                "username": "admin_log", 
                "password_hash": mock_hash("admin_log"), 
                "photo_path": None
            },
            "admin_principal": {
                "name": "Admin Principal (Mock)", 
                "role": "Administrador Total", 
                "username": "admin_principal", 
                "password_hash": mock_hash("admin_principal"), 
                "photo_path": None
            },
            "jefe_ventas": {
                "name": "Jefe de Ventas", 
                "role": "Gerente",
                "username": "jefe_ventas", 
                "password_hash": mock_hash("jefe_ventas"), 
                "photo_path": None
            },
            "maria_perez": {
                "name": "Maria Pérez", 
                "role": "Vendedor",
                "username": "maria_perez", 
                "password_hash": mock_hash("maria_perez"), 
                "photo_path": None
            },
            "carlos_gonzalez": {
                "name": "Carlos González", 
                "role": "Vendedor",
                "username": "carlos_gonzalez", 
                "password_hash": mock_hash("carlos_gonzalez"), 
                "photo_path": None
            },
        }
        if user_id_str not in mock_users:
             mock_users[user_id_str] = {
                 "name": f"Usuario {user_id_str[-4:].upper()}", 
                 "role": self.user_role, 
                 "username": f"user_{user_id_str}", 
                 "password_hash": mock_hash(f"user_{user_id_str}"),
                 "photo_path": None
                }
        return mock_users

    def load_users_data(self):
        """Carga los datos de usuarios (simulados o reales) y actualiza la UI."""
        
        # SIMULACIÓN (MOCK):
        # En una integración real, aquí llamarías: self.users_data = self.db.get_all_users()
        self.users_data = self._get_mock_users() 

        self._refresh_user_tree(self.users_data)
        # Desactivar controles al cargar inicialmente
        self.delete_user_button.configure(state="disabled")
        self.save_role_button.configure(state="disabled")
        self.edit_full_user_button.configure(state="disabled")


    def _refresh_user_tree(self, users_data):
        """Limpia y rellena el Treeview con los datos de usuario proporcionados."""
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
            
        for user_id, data in users_data.items():
            # CORRECCIÓN: Aseguramos que user_id se trata como una cadena
            user_id_str = str(user_id)
            short_id = user_id_str[-4:].upper()
            
            # Usamos la cadena de texto como iid para el Treeview y para el ID corto
            self.users_tree.insert("", "end", iid=user_id_str, 
                                     values=(short_id, data["name"], data["role"]))


    def _on_user_select(self, event):
        """Maneja la selección de un usuario en el Treeview para mostrar sus detalles."""
        selected_item = self.users_tree.focus()
        
        # Lógica para deselección o item no válido
        if not selected_item:
            self.current_selected_user_id = None
            self.edit_user_id.configure(text="Seleccione un usuario", text_color="gray50")
            self.edit_user_name_label.configure(text="")
            self.edit_username_label.configure(text="")
            self.role_combobox.set("Vendedor")
            self.delete_user_button.configure(state="disabled", text="Eliminar Usuario 🗑️")
            self.save_role_button.configure(state="disabled")
            self.edit_full_user_button.configure(state="disabled") 
            return 

        # Se obtiene la clave real del diccionario (el iid es el ID del usuario)
        user_id_key = selected_item 
        user_data = self.users_data.get(user_id_key)
        
        if user_data:
            self.current_selected_user_id = user_id_key
            
            # Actualiza el panel de control lateral
            short_id = user_id_key[-4:].upper()
            self.edit_user_id.configure(text=short_id, text_color="white")
            self.edit_user_name_label.configure(text=user_data["name"])
            self.edit_username_label.configure(text=user_data["username"])
            self.role_combobox.set(user_data["role"])

            # Habilitar botones
            self.delete_user_button.configure(state="normal")
            self.save_role_button.configure(state="normal")
            self.edit_full_user_button.configure(state="normal") 
            
            # Deshabilitar eliminación si es el usuario actualmente logueado (por seguridad)
            if self.current_selected_user_id == str(self.user_id):
                self.delete_user_button.configure(state="disabled", text="No se puede autoeliminar")

    # [MÉTODOS FINALES MANTENIDOS]

    def save_user_role(self):
        """Guarda el rol del usuario seleccionado (función de control rápido)."""
        if not self.current_selected_user_id:
            messagebox.showwarning("Advertencia", "Seleccione un usuario primero.")
            return

        new_role = self.role_combobox.get()
        user_id = self.current_selected_user_id
        
        # 1. Llamada a DB (Actualizar solo el rol)
        # En la DB real, user_id debe ser el ID numérico
        # self.db.update_user_role(user_id, new_role) 

        # 2. Simulación y Refresco
        self.users_data[user_id]['role'] = new_role
        self._refresh_user_tree(self.users_data)
        messagebox.showinfo("Éxito", f"Rol de '{self.users_data[user_id]['name']}' actualizado a '{new_role}'.")

    def delete_user(self):
        """Elimina el usuario seleccionado de la DB."""
        if not self.current_selected_user_id:
            messagebox.showwarning("Advertencia", "Seleccione un usuario primero.")
            return

        user_id = self.current_selected_user_id
        user_name = self.users_data.get(user_id, {}).get('name', 'Usuario Desconocido')

        if not messagebox.askyesno("Confirmar Eliminación", 
                                     f"¿Está seguro de que desea ELIMINAR permanentemente al usuario '{user_name}' (ID: {user_id})?"):
            return

        # 1. Llamada a DB (Eliminar usuario)
        # self.db.delete_user(user_id)
        
        # 2. Simulación y Refresco
        if user_id in self.users_data:
            del self.users_data[user_id]
            self._refresh_user_tree(self.users_data)
            self._on_user_select(None) # Desselecciona y reinicia el panel
            messagebox.showinfo("Éxito", f"Usuario '{user_name}' eliminado correctamente.")
        else:
            messagebox.showerror("Error", "Error al eliminar: el usuario no se encontró en la simulación local.")