import os
import io # Importación nueva y necesaria
import hashlib
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath, QImage
from PyQt6.QtCore import Qt
from PIL import Image, ImageOps # Importación de la librería que instalamos

_DIRECTORIO_CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cache_avatares")

def procesar_avatar_circular(ruta_imagen, tamano):
    """Carga una imagen con Pillow, la endereza infaliblemente usando EXIF, y la hace circular.
    Utiliza una caché en disco para acelerar cargas posteriores de forma instantánea.
    """
    if not ruta_imagen or not os.path.exists(ruta_imagen):
        return None

    ruta_cache = None
    try:
        # 0. VERIFICAR CACHÉ EN DISCO
        os.makedirs(_DIRECTORIO_CACHE, exist_ok=True)
        mtime = int(os.path.getmtime(ruta_imagen))
        hash_ruta = hashlib.md5(f"{ruta_imagen}_{tamano}_{mtime}".encode('utf-8')).hexdigest()
        ruta_cache = os.path.join(_DIRECTORIO_CACHE, f"{hash_ruta}.png")

        if os.path.exists(ruta_cache):
            pix = QPixmap(ruta_cache)
            if not pix.isNull():
                return pix
    except Exception:
        ruta_cache = None

    try:
        # 1. ABRIR Y ENDEREZAR CON PILLOW (La solución real)
        with Image.open(ruta_imagen) as img:
            # Esta función de Pillow es magia pura: lee EXIF y rota los píxeles reales
            img_corregida = ImageOps.exif_transpose(img)
            
            # Preservamos transparencia si existe (RGBA), o RGB si no
            if img_corregida.mode not in ('RGB', 'RGBA'):
                img_corregida = img_corregida.convert('RGBA')

            # 2. CONVERTIR PILLOW A PYQT6
            # Guardamos la imagen corregida en memoria como bytes con formato adecuado
            byte_arr = io.BytesIO()
            formato = 'PNG' if img_corregida.mode == 'RGBA' else 'JPEG'
            img_corregida.save(byte_arr, format=formato)
            byte_data = byte_arr.getvalue()
            
            # Cargamos esos bytes en un QImage de PyQt
            qimage = QImage.fromData(byte_data)
            pixmap_original = QPixmap.fromImage(qimage)

        # 3. LÓGICA DE RECORTE Y CÍRCULO (Igual que antes)
        if pixmap_original.isNull():
            return None

        lado_menor = min(pixmap_original.width(), pixmap_original.height())
        rectangulo_cuadrado = pixmap_original.copy(
            (pixmap_original.width() - lado_menor) // 2,
            (pixmap_original.height() - lado_menor) // 2,
            lado_menor,
            lado_menor
        )

        pixmap_escalado = rectangulo_cuadrado.scaled(
            tamano, tamano, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )

        pixmap_circular = QPixmap(tamano, tamano)
        pixmap_circular.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap_circular)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        path = QPainterPath()
        path.addEllipse(0, 0, tamano, tamano)
        
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap_escalado)
        painter.end()

        # Guardar en caché en disco para reutilización instantánea
        if ruta_cache:
            try:
                pixmap_circular.save(ruta_cache, "PNG")
            except Exception:
                pass

        return pixmap_circular

    except Exception as e:
        print(f"Error crítico procesando avatar con Pillow: {e}")
        return None

def estabilizar_combobox(combo, max_visibles=15):
    """
    Configura un QComboBox para que:
    1. Desactive el autoScroll descontrolado en los bordes del menú desplegable que hace que la lista se desplace sola sin parar.
    2. Ignore la rueda del mouse cuando está cerrado (evita que cambie de item por error al hacer scroll en la pantalla).
    3. Establezca un límite limpio de elementos visibles antes de usar barra de desplazamiento controlada.
    """
    try:
        combo.setMaxVisibleItems(max_visibles)
        # Ignorar scroll del mouse en el combo cerrado para no disparar cambios accidentales tipo ruleta
        combo.wheelEvent = lambda event: event.ignore()
        view = combo.view()
        if view:
            view.setAutoScroll(False)
    except Exception as e:
        print(f"Error estabilizando combobox: {e}")
