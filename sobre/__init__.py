"""Pacote da janela Sobre: dados (info_app), texto (conteudo), ícone (icone_app) e interface (dialogo_sobre)."""

from .dialogo_sobre import DialogoSobre
from .icone_app import carregar_icone

__all__ = ["DialogoSobre", "carregar_icone"]
