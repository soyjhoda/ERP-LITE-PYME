import customtkinter as ctk

# Definiciones de estilo para evitar errores
ACCENT_CYAN = "#00FFFF"       
BACKGROUND_DARK = "#0D1B2A"   

class ConfigPage(ctk.CTkFrame):
    """Placeholder para la página de Configuración."""
    def __init__(self, master, db_manager, user_id):
        super().__init__(master, fg_color=BACKGROUND_DARK)
        self.db = db_manager
        self.user_id = user_id
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="PÁGINA DE CONFIGURACIÓN - FUNCIONALIDAD PENDIENTE", 
                     font=ctk.CTkFont(size=30, weight="bold"), text_color=ACCENT_CYAN).grid(row=0, column=0, padx=200, pady=200)