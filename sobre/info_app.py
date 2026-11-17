"""
Dados do aplicativo exibidos na janela Sobre.

Este arquivo contém apenas informação (sem código de interface).
Para atualizar a janela Sobre, edite os valores abaixo.
"""

from typing import List, Tuple

# =============================================================================
# IDENTIFICAÇÃO
# =============================================================================

NOME = "myGraphDrawer"
SUBTITULO = "Editor e Analisador de Grafos"
VERSAO = "0.1.0"
ANO = 2026
AUTOR = "Thiago de Melo"
TITULO_JANELA = f"{NOME} — {SUBTITULO}"

# Arquivo SVG do ícone, na mesma pasta deste pacote.
ARQUIVO_ICONE = "icone.svg"

# Identificador do app no Windows (barra de tarefas). Sem espaços; se mudar,
# o Windows passa a tratar o app como outro (atalhos fixados se perdem).
ID_APLICATIVO = f"{NOME}.Editor"

# Opcionais: deixe em branco ("") para não exibir na janela.
LICENCA = ""
LINK_PROJETO = ""

# =============================================================================
# DESCRIÇÃO
# =============================================================================

DESCRICAO = (
    "O myGraphDrawer é um editor visual de grafos simples não direcionados. "
    "Você desenha vértices e arestas com o mouse, ou cria o grafo a partir de "
    "uma matriz de adjacência, e o aplicativo calcula propriedades e executa "
    "algoritmos sobre ele."
)

FUNCIONALIDADES: List[str] = [
    "Edição visual: criar, mover e excluir vértices e arestas com o mouse.",
    "Grafos predefinidos: completo, ciclo, caminho, roda, estrela, "
    "bipartido completo, grade, Petersen, sólidos platônicos e Karate Club.",
    "Matrizes de adjacência, incidência e laplaciana, e criação do grafo "
    "a partir de uma matriz de adjacência digitada.",
    "Propriedades: ordem, tamanho, graus, conexidade, planaridade, "
    "bipartição, árvore, euleriano e hamiltoniano.",
    "Algoritmos: caminho mínimo, caminho hamiltoniano, componentes conexas "
    "e pontes.",
    "Layouts automáticos: circular, força, Kamada-Kawai e planar.",
    "Salvar e abrir grafos em JSON e exportar como imagem PNG.",
]

# =============================================================================
# ATALHOS (pares: ação/tecla, efeito)
# =============================================================================

ATALHOS_MOUSE: List[Tuple[str, str]] = [
    ("Clicar no espaço vazio", "Cria um vértice."),
    ("Clicar em um vértice ou aresta", "Seleciona o elemento."),
    ("Arrastar um vértice", "Move o vértice."),
    ("Arrastar uma aresta", "Move os dois vértices da aresta."),
    ("Modo aresta: clicar na origem e depois no destino",
     "Cria a aresta (clicar no espaço vazio cria o vértice)."),
]

ATALHOS_TECLADO: List[Tuple[str, str]] = [
    ("E", "Liga ou desliga o modo aresta."),
    ("Esc", "Cancela a ação atual: origem da aresta, modo aresta ou "
            "seleção e destaques (nessa ordem)."),
    ("Delete", "Exclui a seleção."),
    ("Ctrl+A", "Seleciona tudo."),
    ("Ctrl+N / Ctrl+O / Ctrl+S", "Novo grafo / Abrir JSON / Salvar JSON."),
]

# =============================================================================
# DEPENDÊNCIAS (nome exibido, nome do pacote no pip, para que serve)
# A versão é lida do ambiente em tempo de execução; pacotes ausentes são omitidos.
# =============================================================================

DEPENDENCIAS: List[Tuple[str, str, str]] = [
    ("PyQt6", "PyQt6", "Interface gráfica."),
    ("NetworkX", "networkx", "Estruturas de grafos, algoritmos e layouts."),
    ("NumPy", "numpy", "Matrizes de adjacência, incidência e laplaciana."),
    ("SciPy", "scipy", "Cálculo de layouts (Kamada-Kawai)."),
]
