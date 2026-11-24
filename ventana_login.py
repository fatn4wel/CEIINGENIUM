from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QFormLayout, QFrame, QMessageBox,
    QGraphicsDropShadowEffect, QApplication, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QColor

from backend.auth import verificar_login, actualizar_contrasena
from ventana_principal import VentanaPrincipal

class LoginWorker(QThread):
    """Background thread that validates the user credentials.
    It emits a ``result`` signal with four arguments:
    - ``exito`` (bool): whether the login succeeded
    - ``nombre`` (str): user full name or error message
    - ``ruta_foto`` (str): path to the user's profile picture (empty if login failed)
    - ``cargo`` (str): user role (empty if login failed)
    """
    result = pyqtSignal(bool, str, str, str)

    def __init__(self, lu: str, pw: str):
        super().__init__()
        self.lu = lu
        self.pw = pw

    def run(self):
        try:
            # ``verificar_login`` returns (exito, nombre, ruta_foto, cargo) on success
            exito, nombre, ruta_foto, cargo = verificar_login(self.lu, self.pw)
            if not exito:
                # When login fails, ``nombre`` contains the error message
                self.result.emit(False, nombre, "", "")
            else:
                # Ensure we always pass a string for the photo path (can be None)
                ruta_foto = ruta_foto or ""
                cargo = cargo or ""
                self.result.emit(True, nombre, ruta_foto, cargo)
        except Exception as e:
            # Emit a generic failure signal with the exception text
            self.result.emit(False, f"Error interno: {e}", "", "")

class VentanaLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.inicializar_ui()

    def inicializar_ui(self):
        self.setWindowTitle("CEI Programa - Acceso")
        self.setObjectName("login_window")
        import os, sys
        ruta_logo = os.path.join(sys._MEIPASS, "logo.png") if hasattr(sys, '_MEIPASS') else "logo.png"
        self.setWindowIcon(QIcon(ruta_logo))
        self.setFixedSize(420, 520)
        qr = self.frameGeometry()
        cp = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.addStretch()

        self.login_card = QFrame()
        self.login_card.setObjectName("login_card")
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(25)
        sombra.setOffset(0, 4)
        sombra.setColor(QColor(0, 0, 0, 40))
        self.login_card.setGraphicsEffect(sombra)

        layout_card = QVBoxLayout(self.login_card)
        layout_card.setContentsMargins(40, 40, 40, 40)

        label_titulo = QLabel("BIENVENIDO/A")
        label_titulo.setObjectName("login_title")
        label_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_card.addWidget(label_titulo)

        self.form_layout = QFormLayout()
        self.form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        self.form_layout.setVerticalSpacing(8)

        label_lu = QLabel("Nº Libreta Universitaria")
        label_lu.setObjectName("login_label")
        self.input_lu = QLineEdit()
        self.input_lu.setPlaceholderText("Ej: 321321")
        self.input_lu.setMaxLength(20)
        self.form_layout.addRow(label_lu, self.input_lu)

        label_pass = QLabel("Contraseña")
        label_pass.setObjectName("login_label")
        self.input_pass = QLineEdit()
        self.input_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_pass.setPlaceholderText("••••••••")
        self.form_layout.addRow(label_pass, self.input_pass)

        # Enter key handling
        self.input_lu.returnPressed.connect(self.input_pass.setFocus)
        self.input_pass.returnPressed.connect(self.procesar_login)

        layout_card.addLayout(self.form_layout)
        layout_card.addSpacing(25)

        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(10)

        btn_ingresar = QPushButton("Ingresar")
        btn_ingresar.setObjectName("btn_ingresar")
        btn_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ingresar.clicked.connect(self.procesar_login)
        layout_botones.addWidget(btn_ingresar)

        btn_salir = QPushButton("Salir")
        btn_salir.setObjectName("btn_salir")
        btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salir.clicked.connect(self.close)
        layout_botones.addWidget(btn_salir)

        layout_card.addLayout(layout_botones)
        layout_principal.addWidget(self.login_card, 0, Qt.AlignmentFlag.AlignCenter)
        layout_principal.addStretch()
        self.cargar_estilos()

    def cargar_estilos(self):
        """Carga una sola vez el archivo QSS y lo aplica a la ventana.
        Usa una caché global para evitar lecturas repetidas del disco.
        """
        global _cached_qss
        try:
            import os, sys
            ruta_qss = os.path.join(sys._MEIPASS, "estilos.qss") if hasattr(sys, '_MEIPASS') else "estilos.qss"
            if '_cached_qss' not in globals():
                with open(ruta_qss, "r", encoding='utf-8') as f:
                    _cached_qss = f.read()
            self.setStyleSheet(_cached_qss)
        except Exception as e:
            print(f"Error cargando estilos: {e}")

    def procesar_login(self):
        lu = self.input_lu.text().strip()
        pw = self.input_pass.text().strip()
        if not lu or not pw:
            QMessageBox.warning(self, "Campos Vacíos", "Por favor ingrese LU y contraseña.")
            return
        # Guardar para uso posterior en handle_login_result
        self.lu = lu
        self.pw = pw
        self.login_worker = LoginWorker(lu, pw)
        self.login_worker.result.connect(self.handle_login_result)
        self.login_worker.start()


    def handle_login_result(self, exito, resultado, ruta_foto, cargo):
        if exito:
            # Si el password coincide con el LU, forzar cambio de contraseña
            if getattr(self, 'lu', None) == getattr(self, 'pw', None):
                if not self._cambiar_contraseña_primer_ingreso(self.lu, self.pw):
                    return
            # Ensure ruta_foto is a string (empty if None)
            ruta_foto = ruta_foto or ""
            cargo = cargo or "Estudiante"
            # Open the main window
            self.nueva_ventana = VentanaPrincipal(resultado, self.lu, ruta_foto, cargo)
            self.nueva_ventana.show()
            # Close login window after the main window is displayed
            self.close()
        else:
            QMessageBox.warning(self, "Error", resultado)

    def _cambiar_contraseña_primer_ingreso(self, lu, pw):
        """Flujo de cambio obligatorio de contraseña al primer ingreso.
        Devuelve True si la contraseña se cambió correctamente.
        """
        max_intentos = 3
        for intento in range(1, max_intentos + 1):
            mensaje = f"Intento {intento}/{max_intentos}: Ingrese una nueva contraseña (no puede estar vacía ni igual a su LU):"
            nueva_pw, ok = QInputDialog.getText(
                self,
                "Primer Ingreso - Seguridad",
                mensaje,
                QLineEdit.EchoMode.Password,
            )
            if not ok:
                QMessageBox.warning(self, "Acceso Denegado", "Debe cambiar la contraseña obligatoriamente para ingresar.")
                return False
            nueva_pw = nueva_pw.strip()
            if not nueva_pw:
                QMessageBox.warning(self, "Error", "La contraseña no puede estar vacía.")
                continue
            if nueva_pw == lu:
                QMessageBox.warning(self, "Error de Seguridad", "La nueva contraseña NO puede ser igual a su LU.")
                continue
            actualizar_contrasena(lu, nueva_pw)
            QMessageBox.information(self, "Éxito", "Contraseña actualizada correctamente. ¡Bienvenido!")
            return True
        QMessageBox.critical(self, "Error", "Se excedió el número máximo de intentos para cambiar la contraseña.")
        return False
