#! /usr/bin/env python3
import sys
from PyQt6.QtWidgets import QApplication
from janela_principal import JanelaPrincipal
from sobre import info_app, carregar_icone


def _configurar_windows() -> None:
    """No Windows, um ID próprio faz a barra de tarefas usar o ícone do app
    em vez do ícone do python.exe."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            info_app.ID_APLICATIVO)
    except (AttributeError, OSError):
        pass


def main() -> None:
    _configurar_windows()
    app = QApplication(sys.argv)
    app.setApplicationName(info_app.NOME)
    app.setApplicationVersion(info_app.VERSAO)
    # depois do QApplication: QPixmap exige
    app.setWindowIcon(carregar_icone())

    # app.setStyle("Fusion")

    janela = JanelaPrincipal()
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
