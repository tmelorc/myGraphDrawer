"""
Montagem do conteúdo textual da janela Sobre.

Transforma os dados de `info_app` em HTML (uma função por aba) e em texto
simples (para copiar). Não cria widgets: isso fica em `dialogo_sobre.py`.
"""

import platform
from html import escape
from importlib import metadata
from typing import Iterable, List, Optional, Sequence, Tuple

from PyQt6.QtCore import QT_VERSION_STR

from . import info_app


# =============================================================================
# VERSÕES DO AMBIENTE
# =============================================================================

def _versao_pacote(distribuicao: str) -> Optional[str]:
    try:
        return metadata.version(distribuicao)
    except metadata.PackageNotFoundError:
        return None


def obter_versoes() -> List[Tuple[str, str, str]]:
    """Retorna (nome, versão, descrição) de Python, Qt e das dependências instaladas."""
    linhas = [
        ("Python", platform.python_version(), "Linguagem."),
        ("Qt", QT_VERSION_STR, "Biblioteca gráfica (versão em uso)."),
    ]
    for nome, distribuicao, descricao in info_app.DEPENDENCIAS:
        versao = _versao_pacote(distribuicao)
        if versao is not None:
            linhas.append((nome, versao, descricao))
    return linhas


# =============================================================================
# BLOCOS HTML REUTILIZÁVEIS
# =============================================================================

def _lista(itens: Iterable[str]) -> str:
    return "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in itens) + "</ul>"


def _tabela(cabecalho: Sequence[str], linhas: Iterable[Sequence[str]]) -> str:
    cab = "".join(f"<th align='left'>{escape(c)}</th>" for c in cabecalho)
    corpo = "".join(
        "<tr>" + "".join(f"<td>{escape(c)}</td>" for c in linha) + "</tr>"
        for linha in linhas
    )
    return (
        "<table cellspacing='0' cellpadding='4' width='100%'>"
        f"<tr>{cab}</tr>{corpo}</table>"
    )


# =============================================================================
# ABAS
# =============================================================================

def html_sobre() -> str:
    partes = [
        f"<p>{escape(info_app.DESCRICAO)}</p>",
        "<h3>Funcionalidades</h3>",
        _lista(info_app.FUNCIONALIDADES),
        "<h3>Autoria</h3>",
        f"<p>{escape(info_app.AUTOR)} &copy; {info_app.ANO}</p>",
    ]
    if info_app.LICENCA:
        partes.append(f"<p>Licença: {escape(info_app.LICENCA)}</p>")
    if info_app.LINK_PROJETO:
        url = escape(info_app.LINK_PROJETO, quote=True)
        partes.append(f"<p>Projeto: <a href=\"{url}\">{escape(info_app.LINK_PROJETO)}</a></p>")
    return "".join(partes)


def html_atalhos() -> str:
    return (
        "<h3>Mouse</h3>"
        + _tabela(("Ação", "Efeito"), info_app.ATALHOS_MOUSE)
        + "<h3>Teclado</h3>"
        + _tabela(("Tecla", "Efeito"), info_app.ATALHOS_TECLADO)
    )


def html_tecnologias() -> str:
    return (
        "<h3>Ambiente</h3>"
        + _tabela(("Componente", "Versão", "Uso"), obter_versoes())
    )


# =============================================================================
# TEXTO SIMPLES (botão "Copiar informações")
# =============================================================================

def texto_informacoes() -> str:
    """Resumo em texto puro, útil para relatar problemas."""
    linhas = [f"{info_app.NOME} {info_app.VERSAO}"]
    linhas += [f"{nome}: {versao}" for nome, versao, _ in obter_versoes()]
    linhas.append(f"Sistema: {platform.platform()}")
    return "\n".join(linhas)
