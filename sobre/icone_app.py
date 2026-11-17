"""Localização e carregamento do ícone do aplicativo (SVG)."""

from pathlib import Path

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap

try:
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:  # módulo SVG ausente em algumas instalações Linux
    QSvgRenderer = None

from . import info_app

# Tamanhos gerados a partir do SVG; o Qt escolhe o mais próximo em cada contexto
# (barra de tarefas, título da janela, Alt+Tab, telas de alta densidade).
TAMANHOS = (16, 24, 32, 48, 64, 128, 256)


def caminho_icone() -> Path:
    """Caminho do arquivo SVG, na mesma pasta deste pacote."""
    return Path(__file__).parent / info_app.ARQUIVO_ICONE


def carregar_icone() -> QIcon:
    """
    Cria um QIcon com vários tamanhos a partir do SVG.
    Retorna um ícone vazio se o arquivo ou o módulo SVG não estiverem disponíveis.

    Deve ser chamado depois de criar o QApplication (QPixmap exige isso).
    """
    caminho = caminho_icone()
    if QSvgRenderer is None or not caminho.is_file():
        return QIcon()

    renderizador = QSvgRenderer(str(caminho))
    if not renderizador.isValid():
        return QIcon()

    icone = QIcon()
    for lado in TAMANHOS:
        pixmap = QPixmap(lado, lado)
        pixmap.fill(Qt.GlobalColor.transparent)
        pintor = QPainter(pixmap)
        renderizador.render(pintor, QRectF(0, 0, lado, lado))
        pintor.end()
        icone.addPixmap(pixmap)
    return icone
