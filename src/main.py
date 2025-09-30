import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
from PIL import Image

# --- IMPORTACIONES ---
# Ahora importamos también las funciones de seguridad para usarlas aquí si es necesario
from .db_manager import DatabaseManager, verify_password, hash_password 
from .dashboard import DashboardFrame as Dashboard 
# ---------------------

# Definición de colores
ACCENT_CYAN = "#00FFFF"      
ACCENT_GREEN = "#00c853"     
BACKGROUND_DARK = "#0D1B2A"  
FRAME_MID = "#1B263B"      
FRAME_DARK = "#1B263B"      

LOGO_PATH = "assets/images/logo.png"

def configure_ttk_styles(app):
    """Configura el tema general TTK."""
    style = ttk.Style(app) 
    style.theme_use("clam")

class App(ctk.CTk):
    """Clase principal de la aplicación que maneja el inicio de sesión y la transición al Dashboard."""
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager() 
        self.title("PROFITUS | Inicializando...")
        self.geometry("1200x700") 
        self.resizable(True, True) 
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # Llamada CLAVE para configurar el tema general 'clam'
        configure_ttk_styles(self)
        
        self.current_user_id = None 
        self.current_user_role = None # ¡Nuevo: Almacenaremos el rol!
        
        self.login_frame = self._create_login_frame(self)
        self.login_frame.pack(pady=0, padx=0, fill="both", expand=True)
        self.after(100, lambda: self.title("PROFITUS | Iniciar Sesión"))


    def _create_login_frame(self, master):
        """Crea la interfaz del formulario de inicio de sesión."""
        
        full_frame = ctk.CTkFrame(master, fg_color=BACKGROUND_DARK)
        full_frame.grid_rowconfigure(0, weight=1)
        full_frame.grid_columnconfigure(0, weight=1)
        
        login_container = ctk.CTkFrame(full_frame, fg_color=FRAME_MID, corner_radius=15, width=450, height=550) 
        login_container.grid(row=0, column=0, padx=20, pady=20, sticky="")
        login_container.grid_rowconfigure((0, 7), weight=1)
        login_container.grid_columnconfigure(0, weight=1)
        
        try:
             # Carga del logo
             logo_img = ctk.CTkImage(light_image=Image.open(LOGO_PATH),
                                     dark_image=Image.open(LOGO_PATH),
                                     size=(150, 150)) 
             ctk.CTkLabel(login_container, image=logo_img, text="").grid(row=1, column=0, pady=(40, 5))
        except FileNotFoundError:
             ctk.CTkLabel(login_container, text="[Logo no encontrado]", text_color="red").grid(row=1, column=0, pady=(40, 5))

        ctk.CTkLabel(login_container, text="PROFITUS - ERP Lite", 
                     font=ctk.CTkFont(size=30, weight="bold"), text_color=ACCENT_CYAN).grid(row=2, column=0, pady=(0, 5))
        
        ctk.CTkLabel(login_container, text="ACCESO AL SISTEMA", 
                     font=ctk.CTkFont(size=14), text_color="gray60").grid(row=3, column=0, pady=(0, 30))

        self.username_entry = ctk.CTkEntry(login_container, placeholder_text="👤 USUARIO", width=300, height=40,
                                             fg_color="#2c3e50", border_color=ACCENT_CYAN, border_width=1)
        self.username_entry.grid(row=4, column=0, padx=50, pady=15, sticky="n")

        self.password_entry = ctk.CTkEntry(login_container, placeholder_text="🔑 CONTRASEÑA", show="*", width=300, height=40,
                                             fg_color="#2c3e50", border_color=ACCENT_CYAN, border_width=1)
        self.password_entry.grid(row=5, column=0, padx=50, pady=15, sticky="n")

        login_button = ctk.CTkButton(login_container, text="INGRESAR", command=self.login_event,
                                     width=300, height=45, fg_color=ACCENT_GREEN, hover_color="#008a38",
                                     font=ctk.CTkFont(size=16, weight="bold"))
        login_button.grid(row=6, column=0, padx=50, pady=(20, 10), sticky="n")
        
        self.password_entry.bind("<Return>", lambda event: self.login_event())
        
        ctk.CTkLabel(login_container, text=f"© {datetime.now().year} Gemini & JHOda Studios.", 
                     font=ctk.CTkFont(size=10), text_color="gray50").grid(row=7, column=0, pady=(0, 10), sticky="s")
        
        return full_frame
    
    
    def login_event(self):
        """Maneja la lógica de inicio de sesión, usando la función segura de la DB."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Usamos el nuevo método authenticate_user que verifica el hash
        user_data = self.db.authenticate_user(username, password)
        
        if user_data:
            # Autenticación exitosa
            self.current_user_id = user_data['id'] 
            self.current_user_role = user_data['rol'] # Guardamos el rol del usuario
            
            # Mensaje de bienvenida más específico
            messagebox.showinfo("Éxito", f"¡Bienvenido, {user_data['nombre_completo']}! (Rol: {self.current_user_role})")
            
            # Pasamos el rol al dashboard para controlar la visibilidad de los botones
            self.show_dashboard(self.current_user_role) 
        else:
            # Autenticación fallida
            messagebox.showerror("Error de Autenticación", "Usuario o contraseña incorrectos.")

    def show_dashboard(self, user_role):
        """Muestra el Dashboard principal de la aplicación, reemplazando el login."""
        self.login_frame.destroy() 
        self.title("PROFITUS | ERP Lite para PYMES")
        
        # Pasamos el rol del usuario al Dashboard
        dashboard_frame = Dashboard(self, self.db, self.current_user_id, user_role) 
        dashboard_frame.pack(expand=True, fill="both")
        
    def destroy(self):
        """Cierra la conexión a la base de datos al cerrar la aplicación."""
        self.db.close()
        super().destroy()

# Punto de entrada
def main():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
