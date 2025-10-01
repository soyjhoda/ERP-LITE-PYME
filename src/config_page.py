import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
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
        
        self.grid_rowconfigure(1, weight=1) # El TabView ocupa todo el espacio debajo del título
        self.grid_columnconfigure(0, weight=1)
        
        # Estado para la gestión de usuarios
        self.current_selected_user_id = None
        self.mock_users_data = {} # Para simular datos de usuarios antes de la conexión real

        self._create_widgets()
        self.load_current_rate()
        
        # Configuración inicial del tema ttk para el Treeview
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
        # Solo añadimos la pestaña de usuarios si el rol es Administrador Total
        if self.user_role == "Administrador Total":
            self.tabview.add("Gestión de Usuarios")
            self._setup_users_tab(self.tabview.tab("Gestión de Usuarios"))
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
        tab_frame.grid_rowconfigure(0, weight=0) # Fila de la tarjeta de tasa
        tab_frame.grid_rowconfigure(1, weight=1) # Espacio libre

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
                                            hover_color=ACCENT_CYAN.lower().replace('f', 'e'))
        save_button.grid(row=3, column=0, columnspan=2, pady=(0, 20))

    def _setup_users_tab(self, tab_frame):
        """Configura la pestaña de Gestión de Usuarios (Añadir, Editar Rol, Eliminar)."""
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_rowconfigure(1, weight=1) # El contenido principal ocupa espacio

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

        # Treeview (usando ttk para la tabla con scroll)
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

        # --- Sub-sección Derecha: Controles de Edición ---
        control_frame = ctk.CTkFrame(main_container, fg_color=FRAME_MID, corner_radius=8)
        control_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 15), pady=15)
        control_frame.grid_columnconfigure(0, weight=1)
        
        # Título del panel de control
        ctk.CTkLabel(control_frame, text="Control de Roles", 
                             font=ctk.CTkFont(size=16, weight="bold"), 
                             text_color="white").grid(row=0, column=0, sticky="w", padx=15, pady=(15, 5))

        # ID (solo lectura)
        ctk.CTkLabel(control_frame, text="ID de Usuario:", text_color="gray70").grid(row=1, column=0, sticky="w", padx=15, pady=(10, 0))
        self.edit_user_id = ctk.CTkLabel(control_frame, text="Seleccione un usuario", text_color="gray50")
        self.edit_user_id.grid(row=2, column=0, sticky="w", padx=15, pady=(0, 10))
        
        # Nombre (solo lectura)
        ctk.CTkLabel(control_frame, text="Nombre:", text_color="gray70").grid(row=3, column=0, sticky="w", padx=15, pady=(10, 0))
        self.edit_user_name = ctk.CTkLabel(control_frame, text="", text_color="white")
        self.edit_user_name.grid(row=4, column=0, sticky="w", padx=15, pady=(0, 10))

        # Rol
        ctk.CTkLabel(control_frame, text="Nuevo Rol:", text_color="gray70").grid(row=5, column=0, sticky="w", padx=15, pady=(10, 0))
        self.role_combobox = ctk.CTkComboBox(control_frame, 
                                             values=["Vendedor", "Gerente", "Administrador Total"],
                                             state="readonly")
        self.role_combobox.set("Vendedor")
        self.role_combobox.grid(row=6, column=0, sticky="ew", padx=15, pady=(0, 20))

        # Botón de Guardar
        ctk.CTkButton(control_frame, text="Guardar Cambios", command=self.save_user_role, 
                      fg_color=ACCENT_GREEN, hover_color="#008a38").grid(row=7, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        # Botón de Eliminar (Añadir Advertencia)
        ctk.CTkButton(control_frame, text="Eliminar Usuario 🗑️", command=self.delete_user, 
                      fg_color=ACCENT_RED, hover_color="#8b0000").grid(row=8, column=0, sticky="ew", padx=15, pady=(0, 15))

        self._load_mock_users() # Cargar datos iniciales/reales

    def _setup_security_tab(self, tab_frame):
        """Configura la pestaña de Herramientas y Seguridad (Backup, Info)."""
        tab_frame.grid_columnconfigure(0, weight=1)
        tab_frame.grid_rowconfigure(3, weight=1) # Ajustamos rowconfigure para dar espacio a dos tarjetas

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
        
        # El botón llama a la nueva función de restauración
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
            
    # =======================================================================
    # LÓGICA DE FUNCIONALIDADES - BACKUP Y RESTAURACIÓN
    # =======================================================================

    def create_backup(self):
        """Inicia el proceso de creación de la copia de seguridad."""
        # Restricción: Solo Administradores pueden hacer backup
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
        # Restricción: Solo Administradores pueden restaurar
        if self.user_role != "Administrador Total":
            messagebox.showwarning("Permiso Denegado", "Solo el Administrador Total puede restaurar la base de datos.")
            return

        # Advertencia de seguridad crucial
        if not messagebox.askyesno("Confirmar Restauración (Peligro)", 
                                     "🚨 ¡ADVERTENCIA! Este proceso **REEMPLAZARÁ PERMANENTEMENTE** la base de datos actual.\n"
                                     "Cualquier dato añadido desde el último backup se perderá.\n\n"
                                     "¿Está SEGURO que desea continuar con la restauración?"):
            return # El usuario canceló la operación
        
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
                # Si la restauración es exitosa, pedimos al usuario que reinicie la app
                messagebox.showinfo("Restauración Exitosa", 
                                     f"{message}\n\n"
                                     "***La aplicación DEBE REINICIARSE para cargar los datos restaurados.***")
            else:
                messagebox.showerror("Error de Restauración", f"No se pudo restaurar la base de datos:\n{message}")
                
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error inesperado durante la restauración: {e}")

    # =======================================================================
    # LÓGICA DE FUNCIONALIDADES - GESTIÓN DE USUARIOS (Fase 4 - Preparación)
    # =======================================================================
    
    def _load_mock_users(self):
        """Carga datos de usuarios simulados o reales (al inicio de Fase 4)."""
        # Limpiar datos previos
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
            
        # Simulación de datos para demostración
        self.mock_users_data = {
            "user_a1b2c3d4": {"name": "Admin Principal", "role": "Administrador Total"},
            "user_e5f6g7h8": {"name": "Jefe de Ventas", "role": "Gerente"},
            "user_i9j0k1l2": {"name": "Maria Pérez", "role": "Vendedor"},
            "user_m3n4o5p6": {"name": "Carlos González", "role": "Vendedor"},
        }
        
        # Insertar en el Treeview
        for user_id, data in self.mock_users_data.items():
            short_id = user_id[-4:].upper()
            self.users_tree.insert("", "end", iid=user_id, 
                                     values=(short_id, data["name"], data["role"]))

    def _on_user_select(self, event):
        """Maneja la selección de un usuario en el Treeview para mostrar sus detalles."""
        selected_item = self.users_tree.focus()
        if not selected_item:
            self.current_selected_user_id = None
            self.edit_user_id.configure(text="Seleccione un usuario", text_color="gray50")
            self.edit_user_name.configure(text="")
            self.role_combobox.set("Vendedor")
            return
            
        user_id = selected_item
        self.current_selected_user_id = user_id
        
        # Recuperar datos de la simulación
        data = self.mock_users_data.get(user_id, {"name": "Desconocido", "role": "Vendedor"})
        
        # Actualizar panel de control
        self.edit_user_id.configure(text=user_id[-4:].upper(), text_color="white")
        self.edit_user_name.configure(text=data["name"])
        self.role_combobox.set(data["role"])


    def save_user_role(self):
        """Guarda el nuevo rol del usuario seleccionado (Lógica de Fase 4)."""
        if not self.current_selected_user_id:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un usuario para editar su rol.")
            return

        new_role = self.role_combobox.get()
        user_id = self.current_selected_user_id
        
        # Simulación de la actualización de la DB (pendiente de implementación real en la DB Manager)
        # self.db.update_user_role(user_id, new_role) 
        
        # Actualizar datos simulados
        if user_id in self.mock_users_data:
            self.mock_users_data[user_id]["role"] = new_role
            self._load_mock_users() # Recargar la tabla para reflejar el cambio
            messagebox.showinfo("Éxito", f"Rol de usuario actualizado (Simulación).\n{user_id[-4:].upper()} ahora es: {new_role}")
        else:
            messagebox.showerror("Error", "Usuario no encontrado en la lista.")
            
            
    def delete_user(self):
        """Elimina un usuario (Lógica de Fase 4)."""
        if not self.current_selected_user_id:
            messagebox.showwarning("Advertencia", "Por favor, seleccione un usuario para eliminar.")
            return

        user_id = self.current_selected_user_id
        user_name = self.mock_users_data.get(user_id, {}).get("name", "este usuario")
        
        if not messagebox.askyesno("Confirmar Eliminación", 
                                     f"¿Está seguro que desea eliminar PERMANENTEMENTE al usuario **{user_name}** ({user_id[-4:].upper()})?\n\nEsta acción no se puede deshacer."):
            return

        # Simulación de la eliminación de la DB (pendiente de implementación real)
        # self.db.delete_user(user_id)
        
        if user_id in self.mock_users_data:
            del self.mock_users_data[user_id]
            
            # Limpiar panel de control y recargar lista
            self._load_mock_users() 
            self.current_selected_user_id = None
            self.edit_user_id.configure(text="Seleccione un usuario", text_color="gray50")
            self.edit_user_name.configure(text="")
            self.role_combobox.set("Vendedor")
            
            messagebox.showinfo("Éxito", f"Usuario {user_name} eliminado (Simulación).")
        else:
            messagebox.showerror("Error", "Usuario no encontrado en la lista.")
