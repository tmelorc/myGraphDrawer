from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
import networkx as nx
from PyQt6.QtGui import QAction, QIntValidator
from PyQt6.QtWidgets import QInputDialog, QMenu, QWidget, QDialog, QFormLayout, QSpinBox, QDialogButtonBox, QLineEdit

from canvas_grafo import CanvasGrafo
from layouts import normalizar_layout


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
    dialogo = QDialog(parent)
    dialogo.setWindowTitle("Bipartido Completo (K_{m,n})")
    dialogo.setMinimumWidth(300)

    layout = QFormLayout(dialogo)
    validador = QIntValidator(1, 10, dialogo)

    campo_m = QLineEdit(dialogo)
    campo_m.setValidator(validador)
    campo_m.setPlaceholderText("10 ≥ m ≥ 1")
    campo_m.setText("3")
    campo_m.selectAll()

    campo_n = QLineEdit(dialogo)
    campo_n.setValidator(validador)
    campo_n.setPlaceholderText("10 ≥ n ≥ 1")
    campo_n.setText("3")
    campo_n.selectAll()

    layout.addRow("Tamanho da partição A (m):", campo_m)
    layout.addRow("Tamanho da partição B (n):", campo_n)

    botoes = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
        parent=dialogo,
    )
    botoes.accepted.connect(dialogo.accept)
    botoes.rejected.connect(dialogo.reject)
    layout.addRow(botoes)

    btn_ok = botoes.button(QDialogButtonBox.StandardButton.Ok)

    def _atualizar_estado_ok() -> None:
        ambos_validos = campo_m.hasAcceptableInput() and campo_n.hasAcceptableInput()
        btn_ok.setEnabled(ambos_validos)

    campo_m.textChanged.connect(_atualizar_estado_ok)
    campo_n.textChanged.connect(_atualizar_estado_ok)
    _atualizar_estado_ok()

    campo_m.setFocus()

    # Exibe o diálogo de forma modal e aguarda a resposta do usuário
    if dialogo.exec() != QDialog.DialogCode.Accepted:
        return None

    m, n = int(campo_m.text()), int(campo_n.text())

    g = nx.complete_bipartite_graph(m, n)
    particao_a = list(range(m))
    pos = nx.bipartite_layout(g, particao_a, align="horizontal")
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


@registrar_grafo("Tetraedro")
def _gerar_tetraedro(parent: QWidget):
    g = nx.tetrahedral_graph()
    # Projeção planar clássica: 1 vértice central (0) e triângulo externo (1, 2, 3)
    # pos = nx.shell_layout(g, nlist=[[0], [1, 2, 3]])
    pos = nx.spring_layout(g)
    return g, pos


@registrar_grafo("Octaedro")
def _gerar_octaedro(parent: QWidget):
    g = nx.octahedral_graph()
    # Projeção planar clássica: 1 vértice central (0) e triângulo externo (1, 2, 3)
    pos = nx.spring_layout(g)
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
        pos_pixels = normalizar_layout(
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
