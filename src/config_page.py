import customtkinter as ctk
from tkinter import messagebox
from .utils import is_valid_float

# Definiciones de estilo
ACCENT_CYAN = "#00FFFF"       
ACCENT_GREEN = "#00c853"
ACCENT_RED = "#c0392b"
BACKGROUND_DARK = "#0D1B2A"   
FRAME_MID = "#1B263B"

class ConfigPage(ctk.CTkFrame):
    """Página de Configuración, utilizada principalmente para gestionar la Tasa de Cambio."""
    # Se añade un argumento para la función de callback de actualización
    def __init__(self, master, db_manager, user_id, update_rate_callback): 
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.user_id = user_id
        self.update_rate_callback = update_rate_callback # Guardamos la función para usarla después
        
        self.grid_rowconfigure(1, weight=1) # Espacio flexible debajo de la configuración
        self.grid_columnconfigure(0, weight=1)

        self._create_widgets()
        self.load_current_rate()

    def _create_widgets(self):
        """Crea todos los elementos de la UI para la configuración."""
        
        # Marco Principal de Contenido
        main_frame = ctk.CTkFrame(self, fg_color=BACKGROUND_DARK)
        main_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)

        # Título
        ctk.CTkLabel(main_frame, text="⚙️ CONFIGURACIÓN DEL SISTEMA", 
                     font=ctk.CTkFont(size=26, weight="bold"), 
                     text_color=ACCENT_CYAN).grid(row=0, column=0, sticky="w", pady=(10, 30))

        # --- Sección de Tasa de Cambio ---
        rate_card = ctk.CTkFrame(main_frame, fg_color=FRAME_MID, corner_radius=10)
        rate_card.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        rate_card.grid_columnconfigure((0, 1), weight=1)
        
        ctk.CTkLabel(rate_card, text="Tasa de Cambio (Bs por 1 USD)", 
                     font=ctk.CTkFont(size=18, weight="bold"), 
                     text_color="white").grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(rate_card, text="Valor Actual:", text_color="gray70").grid(row=1, column=0, sticky="w", padx=20, pady=(10, 0))
        
        self.current_rate_label = ctk.CTkLabel(rate_card, text="Cargando...", 
                                               font=ctk.CTkFont(size=22, weight="bold"), 
                                               text_color=ACCENT_GREEN)
        self.current_rate_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 20))
        
        # Entrada para nueva tasa
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
