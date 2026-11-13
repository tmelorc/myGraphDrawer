import sys
from PyQt6.QtWidgets import QApplication
from janela_principal import JanelaPrincipal


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("myGraphDrawer")
    app.setStyle("Fusion")

    janela = JanelaPrincipal()
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
