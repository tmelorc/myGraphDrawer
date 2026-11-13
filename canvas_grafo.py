import math
from typing import Dict, List, Optional, Tuple
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QKeyEvent, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from modelo_grafo import ModeloGrafo


class CanvasGrafo(QWidget):
    """
    Canvas 2D desenhado diretamente via QPainter (paintEvent) usando PyQt6.
    """

    grafo_alterado = pyqtSignal()
    modo_alterado = pyqtSignal(bool)
    mensagem_status = pyqtSignal(str)

    RAIO_VERTICE = 18
    TOLERANCIA_ARESTA = 8.0

    def __init__(self, modelo: ModeloGrafo, parent=None) -> None:
        super().__init__(parent)
        self.modelo: ModeloGrafo = modelo

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(False)

        # Estado de interação
        self.modo_aresta: bool = False
        self._vertice_selecionado: Optional[int] = None
        self._aresta_selecionada: Optional[Tuple[int, int]] = None
        self._origem_aresta: Optional[int] = None

        # Controle de arraste
        self._arrastando_vertice: Optional[int] = None
        self._arrastando_aresta: Optional[Tuple[int, int]] = None
        self._ultimo_x: float = 0.0
        self._ultimo_y: float = 0.0

        # Cores especiais para algoritmos
        self._cores_vertices_alg: Dict[int, QColor] = {}
        self._cores_arestas_alg: Dict[Tuple[int, int], QColor] = {}

        # Recursos gráficos pré-alocados
        self._cor_fundo = QColor("#f8f9fa")
        self._cor_vertice = QColor("#0066cc")
        self._cor_selecionado = QColor("#ff3300")
        self._cor_origem_aresta = QColor("#ff7700")

        self._pen_aresta = QPen(QColor("#333333"), 2.6,
                                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        self._pen_aresta_sel = QPen(
            QColor("#ff3300"), 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        self._pen_borda_vertice = QPen(QColor("#ffffff"), 2.0)
        self._pen_borda_sel = QPen(QColor("#ffffff"), 3.0)
        self._pen_texto = QPen(QColor("#ffffff"))

        self._fonte_vertice = QFont("Sans Serif", 10, QFont.Weight.Bold)

    # =========================================================================
    # 1. CONTROLE DE MODOS E SELEÇÃO
    # =========================================================================

    def definir_modo_aresta(self, ativo: bool) -> None:
        if self.modo_aresta == ativo:
            return
        self.modo_aresta = ativo
        self._origem_aresta = None
        self._limpar_selecao()
        self.modo_alterado.emit(self.modo_aresta)

        if self.modo_aresta:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self.mensagem_status.emit(
                "Modo Aresta (E) ATIVO: Clique no vértice de origem e depois no vértice de destino."
            )
        else:
            self.unsetCursor()
            self.mensagem_status.emit(
                "Modo Padrão: Clique no vazio cria vértice | Arraste vértices/arestas | Del remove."
            )
        self.update()

    def alternar_modo_aresta(self) -> None:
        self.definir_modo_aresta(not self.modo_aresta)

    def _limpar_selecao(self) -> None:
        self._vertice_selecionado = None
        self._aresta_selecionada = None

    def obter_vertices_selecionados(self) -> List[int]:
        return [self._vertice_selecionado] if self._vertice_selecionado is not None else []

    # =========================================================================
    # 2. OPERAÇÕES NO GRAFO
    # =========================================================================

    def criar_vertice(self, x: float, y: float) -> int:
        vid = self.modelo.adicionar_vertice(x, y)
        self.grafo_alterado.emit()
        self.update()
        return vid

    def criar_aresta(self, u: int, v: int) -> bool:
        criada = self.modelo.adicionar_aresta(u, v)
        if criada:
            self.grafo_alterado.emit()
            self.update()
        return criada

    def excluir_selecionados(self) -> None:
        alterou = False
        if self._vertice_selecionado is not None:
            vid = self._vertice_selecionado
            if self._origem_aresta == vid:
                self._origem_aresta = None
            self.modelo.remover_vertice(vid)
            self._vertice_selecionado = None
            alterou = True
        elif self._aresta_selecionada is not None:
            u, v = self._aresta_selecionada
            self.modelo.remover_aresta(u, v)
            self._aresta_selecionada = None
            alterou = True

        if alterou:
            self.limpar_destaques_algoritmos()
            self.grafo_alterado.emit()
            self.update()

    def limpar_tudo(self) -> None:
        self._origem_aresta = None
        self._limpar_selecao()
        self.limpar_destaques_algoritmos()
        self.modelo.limpar()
        self.grafo_alterado.emit()
        self.update()

    def reconstruir_do_modelo(self) -> None:
        self._origem_aresta = None
        self._limpar_selecao()
        self.limpar_destaques_algoritmos()
        self.grafo_alterado.emit()
        self.update()

    # =========================================================================
    # 3. ALGORITMOS VISUAIS
    # =========================================================================

    def limpar_destaques_algoritmos(self) -> None:
        self._cores_vertices_alg.clear()
        self._cores_arestas_alg.clear()
        self.update()

    def destacar_caminho_minimo(self, caminho: List[int]) -> None:
        self.limpar_destaques_algoritmos()
        cor = QColor("#00aa55")
        for vid in caminho:
            self._cores_vertices_alg[vid] = cor
        for i in range(len(caminho) - 1):
            u, v = caminho[i], caminho[i + 1]
            self._cores_arestas_alg[(min(u, v), max(u, v))] = cor
        self.update()

    def colorir_componentes_conexos(self, componentes: List[List[int]]) -> None:
        self.limpar_destaques_algoritmos()
        total = len(componentes)
        if total == 0:
            return
        for idx, comp in enumerate(componentes):
            hue = int((idx * 360) / max(1, total)) % 360
            cor = QColor.fromHsl(hue, 210, 120)
            for vid in comp:
                self._cores_vertices_alg[vid] = cor
            for i in range(len(comp)):
                for j in range(i + 1, len(comp)):
                    chave = (min(comp[i], comp[j]), max(comp[i], comp[j]))
                    if self.modelo.grafo.has_edge(comp[i], comp[j]):
                        self._cores_arestas_alg[chave] = cor
        self.update()

    # =========================================================================
    # 4. DETECÇÃO GEOMÉTRICA
    # =========================================================================

    def _obter_vertice_em(self, x: float, y: float) -> Optional[int]:
        for vid in reversed(self.modelo.vertices_ordenados()):
            vx, vy = self.modelo.posicoes[vid]
            if math.hypot(x - vx, y - vy) <= self.RAIO_VERTICE:
                return vid
        return None

    @staticmethod
    def _distancia_ponto_segmento(px: float, py: float, ax: float, ay: float, bx: float, by: float) -> float:
        dx, dy = bx - ax, by - ay
        l2 = dx * dx + dy * dy
        if l2 == 0:
            return math.hypot(px - ax, py - ay)
        t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
        return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

    def _obter_aresta_em(self, x: float, y: float) -> Optional[Tuple[int, int]]:
        melhor: Optional[Tuple[int, int]] = None
        menor_dist = self.TOLERANCIA_ARESTA
        for u, v in self.modelo.grafo.edges():
            ax, ay = self.modelo.posicoes[u]
            bx, by = self.modelo.posicoes[v]
            dist = self._distancia_ponto_segmento(x, y, ax, ay, bx, by)
            if dist <= menor_dist:
                menor_dist = dist
                melhor = (min(u, v), max(u, v))
        return melhor

    # =========================================================================
    # 5. RENDERIZAÇÃO
    # =========================================================================

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(0, 0, self.width(), self.height(), self._cor_fundo)

        # 1. Arestas
        for u, v in self.modelo.grafo.edges():
            chave = (min(u, v), max(u, v))
            ax, ay = self.modelo.posicoes[u]
            bx, by = self.modelo.posicoes[v]

            if self._aresta_selecionada == chave:
                painter.setPen(self._pen_aresta_sel)
            elif chave in self._cores_arestas_alg:
                pen_alg = QPen(
                    self._cores_arestas_alg[chave], 4.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
                painter.setPen(pen_alg)
            else:
                painter.setPen(self._pen_aresta)

            painter.drawLine(int(ax), int(ay), int(bx), int(by))

        # 2. Vértices
        painter.setFont(self._fonte_vertice)
        r = self.RAIO_VERTICE
        diametro = r * 2

        for vid in self.modelo.vertices_ordenados():
            vx, vy = self.modelo.posicoes[vid]
            x_esq = int(vx - r)
            y_topo = int(vy - r)

            if self._origem_aresta == vid:
                painter.setBrush(self._cor_origem_aresta)
                painter.setPen(self._pen_borda_sel)
            elif self._vertice_selecionado == vid:
                painter.setBrush(self._cor_selecionado)
                painter.setPen(self._pen_borda_sel)
            elif vid in self._cores_vertices_alg:
                painter.setBrush(self._cores_vertices_alg[vid])
                painter.setPen(self._pen_borda_vertice)
            else:
                painter.setBrush(self._cor_vertice)
                painter.setPen(self._pen_borda_vertice)

            painter.drawEllipse(x_esq, y_topo, diametro, diametro)

            painter.setPen(self._pen_texto)
            painter.drawText(x_esq, y_topo, diametro, diametro,
                             Qt.AlignmentFlag.AlignCenter, str(vid))

        painter.end()

    # =========================================================================
    # 6. EVENTOS DE MOUSE E TECLADO
    # =========================================================================

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus()
        if event.button() != Qt.MouseButton.LeftButton:
            return

        x = float(event.position().x())
        y = float(event.position().y())
        vertice_clicado = self._obter_vertice_em(x, y)

        if self.modo_aresta:
            if self._origem_aresta is None:
                self._origem_aresta = vertice_clicado if vertice_clicado is not None else self.criar_vertice(
                    x, y)
                self.mensagem_status.emit(
                    f"Origem: vértice {self._origem_aresta}. Clique no vértice de destino (ou no vazio para criar)."
                )
            else:
                if vertice_clicado == self._origem_aresta:
                    self._origem_aresta = None
                    self.mensagem_status.emit("Seleção de origem cancelada.")
                else:
                    destino = vertice_clicado if vertice_clicado is not None else self.criar_vertice(
                        x, y)
                    criada = self.criar_aresta(self._origem_aresta, destino)
                    if criada:
                        self.mensagem_status.emit(
                            f"Aresta {{{self._origem_aresta}, {destino}}} criada.")
                    else:
                        self.mensagem_status.emit(
                            f"Aresta entre {self._origem_aresta} e {destino} já existe.")
                    self._origem_aresta = None
            self.update()
            return

        # Modo Padrão
        self.limpar_destaques_algoritmos()

        if vertice_clicado is not None:
            self._limpar_selecao()
            self._vertice_selecionado = vertice_clicado
            self._arrastando_vertice = vertice_clicado
            self.update()
            return

        aresta_clicada = self._obter_aresta_em(x, y)
        if aresta_clicada is not None:
            self._limpar_selecao()
            self._aresta_selecionada = aresta_clicada
            self._arrastando_aresta = aresta_clicada
            self._ultimo_x = x
            self._ultimo_y = y
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.update()
            return

        # Clicou no vazio: cria vértice
        self._limpar_selecao()
        novo_vid = self.criar_vertice(x, y)
        self._vertice_selecionado = novo_vid
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        x = float(event.position().x())
        y = float(event.position().y())

        if self._arrastando_vertice is not None:
            vid = self._arrastando_vertice
            if vid in self.modelo.posicoes:
                self.modelo.atualizar_posicao(vid, x, y)
                self.update()
            return

        if self._arrastando_aresta is not None:
            u, v = self._arrastando_aresta
            dx = x - self._ultimo_x
            dy = y - self._ultimo_y
            self._ultimo_x = x
            self._ultimo_y = y

            if u in self.modelo.posicoes and v in self.modelo.posicoes:
                ux, uy = self.modelo.posicoes[u]
                vx, vy = self.modelo.posicoes[v]
                self.modelo.atualizar_posicao(u, ux + dx, uy + dy)
                self.modelo.atualizar_posicao(v, vx + dx, vy + dy)
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._arrastando_vertice = None
            if self._arrastando_aresta is not None:
                self._arrastando_aresta = None
                if not self.modo_aresta:
                    self.unsetCursor()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_E:
            self.alternar_modo_aresta()
        elif event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self.excluir_selecionados()
        elif event.key() == Qt.Key.Key_Escape:
            if self._origem_aresta is not None:
                self._origem_aresta = None
            elif self.modo_aresta:
                self.definir_modo_aresta(False)
            else:
                self._limpar_selecao()
                self.limpar_destaques_algoritmos()
            self.update()
        else:
            super().keyPressEvent(event)
