"""Janela "Sobre" do aplicativo (somente interface; o texto vem de `conteudo`)."""

from typing import Optional

from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

try:
    from PyQt6.QtSvgWidgets import QSvgWidget
except ImportError:  # módulo SVG ausente em algumas instalações Linux
    QSvgWidget = None

from . import conteudo, info_app
from .icone_app import caminho_icone

TAMANHO_ICONE = 96


class DialogoSobre(QDialog):
    """Diálogo modal com descrição, atalhos e versões das tecnologias usadas."""

    _ROTULO_COPIAR = "Copiar informações"

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Sobre o {info_app.NOME}")
        self.setMinimumSize(540, 480)

        layout = QVBoxLayout(self)
        layout.addWidget(self._criar_cabecalho())

        abas = QTabWidget(self)
        abas.addTab(self._criar_navegador(conteudo.html_sobre()), "Sobre")
        abas.addTab(self._criar_navegador(conteudo.html_atalhos()), "Atalhos")
        abas.addTab(self._criar_navegador(
            conteudo.html_tecnologias()), "Tecnologias")
        layout.addWidget(abas, 1)

        botoes = QDialogButtonBox(self)
        self._btn_copiar = botoes.addButton(
            self._ROTULO_COPIAR, QDialogButtonBox.ButtonRole.ActionRole)
        self._btn_copiar.clicked.connect(self._copiar_informacoes)
        botoes.addButton(QDialogButtonBox.StandardButton.Close)
        botoes.rejected.connect(self.reject)
        layout.addWidget(botoes)

        # Timer filho do diálogo: é destruído junto com ele, sem risco de
        # tocar no botão depois que a janela foi fechada.
        self._timer_copiado = QTimer(self)
        self._timer_copiado.setSingleShot(True)
        self._timer_copiado.timeout.connect(
            lambda: self._btn_copiar.setText(self._ROTULO_COPIAR))

    # -------------------------------------------------------------------------

    def _criar_cabecalho(self) -> QWidget:
        cabecalho = QWidget(self)
        layout = QVBoxLayout(cabecalho)
        layout.setContentsMargins(0, 0, 0, 4)

        icone = self._criar_icone()
        if icone is not None:
            layout.addWidget(icone, alignment=Qt.AlignmentFlag.AlignCenter)

        titulo = QLabel(info_app.NOME)
        fonte = titulo.font()
        fonte.setPointSize(fonte.pointSize() + 10)
        fonte.setBold(True)
        titulo.setFont(fonte)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitulo = QLabel(f"{info_app.SUBTITULO} — versão {info_app.VERSAO}")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(titulo)
        layout.addWidget(subtitulo)
        return cabecalho

    @staticmethod
    def _criar_icone() -> Optional[QWidget]:
        """Carrega o SVG do ícone; sem o arquivo ou o módulo SVG, a janela abre sem ele."""
        caminho = caminho_icone()
        if QSvgWidget is None or not caminho.is_file():
            return None
        icone = QSvgWidget(str(caminho))
        icone.setFixedSize(QSize(TAMANHO_ICONE, TAMANHO_ICONE))
        return icone

    @staticmethod
    def _criar_navegador(html: str) -> QTextBrowser:
        navegador = QTextBrowser()
        navegador.setOpenExternalLinks(True)
        navegador.setHtml(html)
        return navegador

    def _copiar_informacoes(self) -> None:
        QApplication.clipboard().setText(conteudo.texto_informacoes())
        self._btn_copiar.setText("Copiado!")
        self._timer_copiado.start(1500)
