import os
import json
import sys

ARCHIVO_CONFIG = "config_seguridad.json"

CONFIG_DEFAULT = {
    "_comentario": "Configuración de contraseñas del sistema. Las claves maestras desbloquean CUALQUIER módulo administrativo. Las claves de roles permiten accesos específicos. Puedes agregar dos o más contraseñas por lista.",
    "claves_maestras": [
        "20VERTEX26",
    ],
    "claves_roles": {
        "rrhh": [
            "4RRHH2026",
        ],
        "hacienda": [
            "HACIENDA2026",
        ],
        "comision": [
            "Comision2026"
        ],
        "configuracion": [
            "Ingeniumcei26",
        ],
        "informatica": [
            "3INFORMATICA2026",
        ]
    }
}

def obtener_ruta_config():
    """
    Localiza la ruta del archivo config_seguridad.json.
    Busca en el directorio de ejecución (o junto al .exe si está empaquetado)
    o en la raíz del proyecto.
    """
    # 1. Si está empaquetado con PyInstaller
    if getattr(sys, 'frozen', False):
        ruta_exe = os.path.dirname(sys.executable)
        return os.path.join(ruta_exe, ARCHIVO_CONFIG)
    
    # 2. Ruta relativa a la raíz del proyecto
    directorio_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(directorio_raiz, ARCHIVO_CONFIG)

def cargar_config_seguridad():
    """
    Carga la configuración desde config_seguridad.json.
    Si el archivo no existe, lo crea automáticamente con los valores por defecto.
    """
    ruta = obtener_ruta_config()
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                datos = json.load(f)
                if isinstance(datos, dict) and "claves_maestras" in datos:
                    return datos
        except Exception as e:
            print(f"Advertencia: no se pudo leer {ARCHIVO_CONFIG}: {e}")
    
    # Si no existe o está corrupto, crear con valores por defecto
    try:
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(CONFIG_DEFAULT, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Advertencia: no se pudo crear {ARCHIVO_CONFIG}: {e}")
        
    return CONFIG_DEFAULT

def obtener_claves_permitidas(rol="general"):
    """
    Devuelve un conjunto (set) con todas las contraseñas válidas para un rol:
    incluye TODAS las contraseñas maestras + las contraseñas asignadas al rol.
    """
    config = cargar_config_seguridad()
    claves = set(config.get("claves_maestras", []))
    
    rol_clean = str(rol).lower().strip()
    claves_rol = config.get("claves_roles", {}).get(rol_clean, [])
    if not claves_rol:
        claves_rol = CONFIG_DEFAULT.get("claves_roles", {}).get(rol_clean, [])
    claves.update(claves_rol)
    
    return claves

def validar_contrasena(password_ingresada, rol="general"):
    """
    Verifica si la contraseña ingresada es válida:
    - Retorna True si coincide con CUALQUIERA de las contraseñas maestras.
    - Retorna True si coincide con CUALQUIERA de las contraseñas del rol especificado.
    - Retorna False en caso contrario.
    Nota: Los accesos personales (login individual) no utilizan esta función.
    """
    if not password_ingresada:
        return False
        
    pwd_clean = password_ingresada.strip()
    claves_validas = obtener_claves_permitidas(rol)
    return pwd_clean in claves_validas
