from typing import Callable, Optional, Set, TYPE_CHECKING
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsItem,
    QGraphicsLineItem,
    QGraphicsSceneHoverEvent,
    QGraphicsSceneMouseEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)

if TYPE_CHECKING:
    from canvas_grafo import CenaGrafo


class ArestaItem(QGraphicsLineItem):
    """
    Representa visualmente uma aresta não-direcionada entre dois VerticeItem.
    Usa QGraphicsLineItem puro (100% C++ nativo) sem QPainterPathStroker.
    """

    COR_PADRAO = QColor("#333333")
    COR_HOVER = QColor("#ff7700")
    COR_SELECIONADA = QColor("#ff3300")
    COR_DESTAQUE_ALG = QColor("#00aa55")

    def __init__(self, origem: "VerticeItem", destino: "VerticeItem") -> None:
        super().__init__()
        self.origem: "VerticeItem" = origem
        self.destino: "VerticeItem" = destino

        self.origem.adicionar_aresta_visual(self)
        self.destino.adicionar_aresta_visual(self)

        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)

        self._hover_direto: bool = False
        self._hover_vizinhanca: bool = False
        self._cor_algoritmo: Optional[QColor] = None

        self.atualizar_geometria()

    def atualizar_geometria(self) -> None:
        p1 = self.origem.scenePos()
        p2 = self.destino.scenePos()
        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

    def definir_hover_direto(self, ativo: bool) -> None:
        if self._hover_direto != ativo:
            self._hover_direto = ativo
            self.update()

    def definir_destaque_vizinhanca(self, ativo: bool) -> None:
        self._hover_vizinhanca = ativo
        self.update()

    def definir_cor_algoritmo(self, cor: Optional[QColor]) -> None:
        self._cor_algoritmo = cor
        self.update()

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.isSelected():
            cor = self.COR_SELECIONADA
            largura = 4.5
        elif self._hover_direto or self._hover_vizinhanca:
            cor = self.COR_HOVER
            largura = 4.0
        elif self._cor_algoritmo is not None:
            cor = self._cor_algoritmo
            largura = 4.5
        else:
            cor = self.COR_PADRAO
            largura = 2.8

        pen = QPen(cor, largura, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(self.line())


class VerticeItem(QGraphicsEllipseItem):
    """
    Representa visualmente um vértice numerado (0 a N) no grafo.
    """

    RAIO = 18.0

    COR_PADRAO = QColor("#0066cc")
    COR_HOVER = QColor("#0099ff")
    COR_VIZINHO = QColor("#ff8800")
    COR_SELECIONADO = QColor("#ff3300")

    def __init__(
        self,
        vid: int,
        x: float,
        y: float,
        on_posicao_alterada: Optional[Callable[[
            int, float, float], None]] = None,
    ) -> None:
        super().__init__(-self.RAIO, -self.RAIO, self.RAIO * 2, self.RAIO * 2)
        self.vid: int = vid
        self.arestas: Set[ArestaItem] = set()
        self._on_posicao_alterada = on_posicao_alterada

        self.setPos(x, y)
        self.setZValue(2)

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)

        self._hover_direto: bool = False
        self._hover_vizinho: bool = False
        self._origem_aresta_ativa: bool = False
        self._cor_algoritmo: Optional[QColor] = None

        self._fonte = QFont("Sans Serif", 10, QFont.Weight.Bold)

    def adicionar_aresta_visual(self, aresta: ArestaItem) -> None:
        self.arestas.add(aresta)

    def remover_aresta_visual(self, aresta: ArestaItem) -> None:
        self.arestas.discard(aresta)

    def definir_origem_aresta(self, ativo: bool) -> None:
        self._origem_aresta_ativa = ativo
        self.update()

    def definir_destaque_vizinho(self, ativo: bool) -> None:
        self._hover_vizinho = ativo
        self.update()

    def definir_cor_algoritmo(self, cor: Optional[QColor]) -> None:
        self._cor_algoritmo = cor
        self.update()

    def _propagacao_hover_vizinhanca(self, ativo: bool) -> None:
        for aresta in self.arestas:
            aresta.definir_destaque_vizinhanca(ativo)
            vizinho = aresta.destino if aresta.origem is self else aresta.origem
            vizinho.definir_destaque_vizinho(ativo)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            for aresta in self.arestas:
                aresta.atualizar_geometria()
            if self._on_posicao_alterada is not None:
                pos: QPointF = value
                self._on_posicao_alterada(self.vid, pos.x(), pos.y())
        return super().itemChange(change, value)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Optional[QWidget] = None,
    ) -> None:
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self._origem_aresta_ativa or self.isSelected():
            cor_fundo = self.COR_SELECIONADO
        elif self._hover_direto:
            cor_fundo = self.COR_HOVER
        elif self._hover_vizinho:
            cor_fundo = self.COR_VIZINHO
        elif self._cor_algoritmo is not None:
            cor_fundo = self._cor_algoritmo
        else:
            cor_fundo = self.COR_PADRAO

        borda_largura = 3.0 if (
            self.isSelected() or self._origem_aresta_ativa) else 2.2
        painter.setPen(QPen(QColor("#ffffff"), borda_largura))
        painter.setBrush(QBrush(cor_fundo))
        painter.drawEllipse(self.rect())

        painter.setPen(QPen(QColor("#ffffff")))
        painter.setFont(self._fonte)
        painter.drawText(QRectF(self.rect()),
                         Qt.AlignmentFlag.AlignCenter, str(self.vid))

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hover_direto = True
        self._propagacao_hover_vizinhanca(True)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent) -> None:
        self._hover_direto = False
        self._propagacao_hover_vizinhanca(False)
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        cena: Optional["CenaGrafo"] = self.scene()  # type: ignore
        if cena and getattr(cena, "modo_aresta", False):
            event.ignore()
            return
        super().mousePressEvent(event)
