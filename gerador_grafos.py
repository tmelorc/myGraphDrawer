# bug: layout do grafo caminho está errado, todo vértice na mesma coord.
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
import networkx as nx
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QInputDialog, QMenu, QWidget

from canvas_grafo import CanvasGrafo


@dataclass
class DefinicaoGrafo:
    nome: str
    gerador: Callable[[QWidget],
                      Optional[Tuple[nx.Graph, Dict[int, Tuple[float, float]]]]]
    separador_antes: bool = False


_CATALOGO_GRAFOS: List[DefinicaoGrafo] = []


def registrar_grafo(nome: str, separador_antes: bool = False):
    """Decorador para cadastrar novos grafos predefinidos no menu."""
    def decorador(func: Callable[[QWidget], Optional[Tuple[nx.Graph, Dict[int, Tuple[float, float]]]]]):
        _CATALOGO_GRAFOS.append(DefinicaoGrafo(
            nome=nome, gerador=func, separador_antes=separador_antes))
        return func
    return decorador


def _normalizar_layout(
    pos_nx: Dict[int, Tuple[float, float]],
    largura: float,
    altura: float,
    margem: float = 70.0,
) -> Dict[int, Tuple[float, float]]:
    """
    Converte as coordenadas normalizadas do NetworkX (geralmente em [-1, 1] ou [0, 1])
    para as coordenadas em pixels do CanvasGrafo, centralizando e respeitando margens.
    """
    if not pos_nx:
        return {}

    if len(pos_nx) == 1:
        unico = next(iter(pos_nx))
        return {unico: (largura / 2.0, altura / 2.0)}

    xs = [float(p[0]) for p in pos_nx.values()]
    ys = [float(p[1]) for p in pos_nx.values()]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    span_x = max_x - min_x
    span_y = max_y - min_y

    area_w = max(120.0, largura - 2.0 * margem)
    area_h = max(120.0, altura - 2.0 * margem)

    # Mantém a proporção (aspect ratio) do layout original do NetworkX
    # escala_x = area_w / span_x if span_x > 1e-9 else 1.0
    # escala_y = area_h / span_y if span_y > 1e-9 else 1.0
    # escala = min(escala_x, escala_y)

    # Mantém a proporção (aspect ratio) do layout original do NetworkX,
    # ignorando eixos degenerados (onde todos os pontos estão alinhados)
    escalas_validas = []
    if span_x > 1e-9:
        escalas_validas.append(area_w / span_x)
    if span_y > 1e-9:
        escalas_validas.append(area_h / span_y)

    escala = min(escalas_validas) if escalas_validas else 1.0

    centro_nx_x = (min_x + max_x) / 2.0
    centro_nx_y = (min_y + max_y) / 2.0
    centro_canvas_x = largura / 2.0
    centro_canvas_y = altura / 2.0

    posicoes_pixel: Dict[int, Tuple[float, float]] = {}
    for vid, (nx_x, nx_y) in pos_nx.items():
        px = centro_canvas_x + (float(nx_x) - centro_nx_x) * escala
        # No Qt o eixo Y cresce para baixo, então invertemos o Y matemático do NetworkX
        py = centro_canvas_y - (float(nx_y) - centro_nx_y) * escala
        posicoes_pixel[int(vid)] = (px, py)

    return posicoes_pixel


# =============================================================================
# CATÁLOGO DE GRAFOS PREDEFINIDOS (NETWORKX + LAYOUTS NATIVOS)
# =============================================================================

@registrar_grafo("Completo (K_n)...")
def _gerar_completo(parent: QWidget):
    n, ok = QInputDialog.getInt(
        parent, "Grafo Completo", "Número de vértices (n):", 5, 1, 30, 1)
    if not ok:
        return None
    g = nx.complete_graph(n)
    pos = nx.circular_layout(g)
    return g, pos


@registrar_grafo("Ciclo (C_n)...")
def _gerar_ciclo(parent: QWidget):
    n, ok = QInputDialog.getInt(
        parent, "Grafo Ciclo", "Número de vértices (n):", 6, 3, 40, 1)
    if not ok:
        return None
    g = nx.cycle_graph(n)
    pos = nx.circular_layout(g)
    return g, pos


@registrar_grafo("Caminho (P_n)...")
def _gerar_caminho(parent: QWidget):
    n, ok = QInputDialog.getInt(
        parent, "Grafo Caminho", "Número de vértices (n):", 5, 2, 40, 1)
    if not ok:
        return None
    g = nx.path_graph(n)
    # Disposição linear horizontal limpa
    pos = {i: (float(i), 0.0) for i in range(n)}
    return g, pos


@registrar_grafo("Roda (W_n)...")
def _gerar_roda(parent: QWidget):
    n, ok = QInputDialog.getInt(
        parent, "Grafo Roda", "Total de vértices (n ≥ 4):", 6, 4, 35, 1)
    if not ok:
        return None
    g = nx.wheel_graph(n)
    # Centro no nó 0 e anel externo circular nos nós 1..n-1
    pos = nx.shell_layout(g, nlist=[[0], list(range(1, n))])
    return g, pos


@registrar_grafo("Estrela (S_k)...")
def _gerar_estrela(parent: QWidget):
    k, ok = QInputDialog.getInt(
        parent, "Grafo Estrela", "Número de folhas (k):", 6, 2, 35, 1)
    if not ok:
        return None
    g = nx.star_graph(k)
    pos = nx.shell_layout(g, nlist=[[0], list(range(1, k + 1))])
    return g, pos


@registrar_grafo("Bipartido Completo (K_{m,n})...", separador_antes=True)
def _gerar_bipartido_completo(parent: QWidget):
    m, ok1 = QInputDialog.getInt(
        parent, "Bipartido Completo", "Tamanho da partição A (m):", 3, 1, 20, 1)
    if not ok1:
        return None
    n, ok2 = QInputDialog.getInt(
        parent, "Bipartido Completo", "Tamanho da partição B (n):", 3, 1, 20, 1)
    if not ok2:
        return None
    g = nx.complete_bipartite_graph(m, n)
    particao_a = list(range(m))
    pos = nx.bipartite_layout(g, particao_a, align="vertical")
    return g, pos


@registrar_grafo("Grade 2D (Grid m × n)...")
def _gerar_grade(parent: QWidget):
    linhas, ok1 = QInputDialog.getInt(
        parent, "Grafo Grade", "Número de linhas:", 3, 2, 15, 1)
    if not ok1:
        return None
    colunas, ok2 = QInputDialog.getInt(
        parent, "Grafo Grade", "Número de colunas:", 4, 2, 15, 1)
    if not ok2:
        return None
    g_tuplas = nx.grid_2d_graph(linhas, colunas)
    # Converte nós de tupla (r, c) para inteiros 0..N-1 mantendo coordenadas de grade
    mapeamento = {no: idx for idx, no in enumerate(sorted(g_tuplas.nodes()))}
    g = nx.relabel_nodes(g_tuplas, mapeamento)
    pos = {idx: (float(c), float(-r)) for (r, c), idx in mapeamento.items()}
    return g, pos


@registrar_grafo("Grafo de Petersen", separador_antes=True)
def _gerar_petersen(parent: QWidget):
    g = nx.petersen_graph()
    # Layout clássico: pentágono externo (0..4) e pentagrama interno (5..9)
    pos = nx.shell_layout(g, nlist=[list(range(5, 10)), list(range(0, 5))])
    return g, pos


@registrar_grafo("Cubo (Q_3)")
def _gerar_cubo(parent: QWidget):
    g = nx.cubical_graph()
    pos = nx.spring_layout(g, seed=42)
    return g, pos


@registrar_grafo("Dodecaedro")
def _gerar_dodecaedro(parent: QWidget):
    g = nx.dodecahedral_graph()
    pos = nx.kamada_kawai_layout(g)
    return g, pos


@registrar_grafo("Icosaedro")
def _gerar_icosaedro(parent: QWidget):
    g = nx.icosahedral_graph()
    pos = nx.kamada_kawai_layout(g)
    return g, pos


@registrar_grafo("Karate Club (Zachary)")
def _gerar_karate(parent: QWidget):
    g = nx.karate_club_graph()
    pos = nx.spring_layout(g, seed=42)
    return g, pos


# =============================================================================
# GERENCIADOR MODULAR PARA PLUGAR NA JANELA PRINCIPAL
# =============================================================================

class GerenciadorGrafosPredefinidos:
    """
    Classe independente que cria o menu 'Grafos' na barra de menus e injeta
    grafos gerados pelo NetworkX diretamente no CanvasGrafo e no ModeloGrafo.
    """

    def __init__(self, janela_principal: QWidget, canvas: CanvasGrafo) -> None:
        self.janela = janela_principal
        self.canvas = canvas
        self._acoes: List[QAction] = []

    def instalar_no_menubar(self, barra_menu) -> QMenu:
        """Cria e retorna o menu 'Grafos' populado com todo o catálogo."""
        menu_grafos = barra_menu.addMenu("&Grafos")

        for item in _CATALOGO_GRAFOS:
            if item.separador_antes:
                menu_grafos.addSeparator()

            acao = QAction(item.nome, self.janela)
            acao.triggered.connect(
                lambda checked=False, definicao=item: self._aplicar_grafo(definicao))
            menu_grafos.addAction(acao)
            self._acoes.append(acao)

        return menu_grafos

    def _aplicar_grafo(self, definicao: DefinicaoGrafo) -> None:
        resultado = definicao.gerador(self.janela)
        if resultado is None:
            return

        grafo_nx, pos_nx = resultado

        # Garante que os IDs dos nós sejam inteiros sequenciais 0..N-1
        nos_ordenados = sorted(grafo_nx.nodes())
        mapa_ids = {no_orig: idx for idx, no_orig in enumerate(nos_ordenados)}

        grafo_limpo = nx.Graph()
        grafo_limpo.add_nodes_from(range(len(nos_ordenados)))
        for u, v in grafo_nx.edges():
            grafo_limpo.add_edge(mapa_ids[u], mapa_ids[v])

        pos_mapeada = {mapa_ids[no]: coords for no, coords in pos_nx.items()}
        pos_pixels = _normalizar_layout(
            pos_mapeada,
            largura=float(max(400, self.canvas.width())),
            altura=float(max(300, self.canvas.height())),
        )

        # Atualiza o modelo e dispara a atualização automática do canvas e do sidepanel
        modelo = self.canvas.modelo
        modelo.grafo = grafo_limpo
        modelo.posicoes = pos_pixels
        modelo._proximo_id = len(nos_ordenados)

        self.canvas.reconstruir_do_modelo()
        self.canvas.mensagem_status.emit(
            f"Grafo '{definicao.nome.replace('...', '')}' carregado "
            f"({grafo_limpo.number_of_nodes()} vértices, {grafo_limpo.number_of_edges()} arestas).", 3000
        )
