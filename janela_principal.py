import numpy as np
from typing import List
from PyQt6.QtCore import Qt
# from PyQt6.QtGui import QAction, QColor, QKeySequence
from PyQt6.QtGui import QAction, QColor, QFontDatabase, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# from modelo_grafo import ModeloGrafo
# from gerador_grafos import GerenciadorGrafosPredefinidos

from canvas_grafo import CanvasGrafo
from modelo_grafo import ModeloGrafo, parsear_texto_matriz
from gerador_grafos import GerenciadorGrafosPredefinidos, normalizar_layout
from layouts import LAYOUTS
from sobre import DialogoSobre, info_app

LIMITE_VERTICES_MATRIZ = 60


class JanelaPrincipal(QMainWindow):
    """
    Janela principal do myGraphDrawer em PyQt6.
    """

    def __init__(self) -> None:
        super().__init__()
        # self.setWindowTitle("myGraphDrawer — Editor e Analisador de Grafos")
        self.setWindowTitle(info_app.TITULO_JANELA)
        self.resize(1200, 900)

        self._arquivo_atual: str = ""

        self.modelo = ModeloGrafo()
        self.cena = CanvasGrafo(self.modelo, self)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self.cena)

        painel_direito = self._criar_painel_analise()
        splitter.addWidget(painel_direito)

        splitter.setSizes([840, 400])
        splitter.setCollapsible(0, False)
        self.setCentralWidget(splitter)

        self._criar_acoes()
        self._criar_menus()
        self._criar_toolbar()
        self._criar_statusbar()

        self.cena.grafo_alterado.connect(self.atualizar_painel_analise)
        self.cena.modo_alterado.connect(self._ao_alterar_modo)
        # self.cena.mensagem_status.connect(self._exibir_mensagem_status)
        self.cena.mensagem_status.connect(self.statusBar().showMessage)

        self.atualizar_painel_analise()

    # =========================================================================
    # 1. AÇÕES, MENUS E BARRA DE FERRAMENTAS
    # =========================================================================

    def _criar_acoes(self) -> None:
        self.acao_novo = QAction("Novo Grafo", self)
        self.acao_novo.setShortcut(QKeySequence.StandardKey.New)
        self.acao_novo.triggered.connect(self.novo_grafo)

        self.acao_abrir = QAction("Abrir JSON...", self)
        self.acao_abrir.setShortcut(QKeySequence.StandardKey.Open)
        self.acao_abrir.triggered.connect(self.abrir_json)

        self.acao_salvar = QAction("Salvar JSON...", self)
        self.acao_salvar.setShortcut(QKeySequence.StandardKey.Save)
        self.acao_salvar.triggered.connect(self.salvar_json)

        self.acao_salvar_csv = QAction("Exportar Matriz CSV...", self)
        self.acao_salvar_csv.triggered.connect(self.salvar_matriz_csv)

        self.acao_exportar_png = QAction("Exportar PNG...", self)
        self.acao_exportar_png.triggered.connect(self.exportar_png)

        self.acao_sair = QAction("Sair", self)
        self.acao_sair.setShortcut(QKeySequence.StandardKey.Quit)
        self.acao_sair.triggered.connect(self.close)

        self.acao_modo_aresta = QAction("Modo Aresta (E)", self)
        self.acao_modo_aresta.setShortcut("E")
        self.acao_modo_aresta.setCheckable(True)
        self.acao_modo_aresta.triggered.connect(self.cena.definir_modo_aresta)

        self.acao_excluir = QAction("Excluir Selecionado", self)
        self.acao_excluir.setShortcut("Delete")
        self.acao_excluir.triggered.connect(self.cena.excluir_selecionados)

        self.acao_caminho_minimo = QAction("Caminho Mínimo...", self)
        self.acao_caminho_minimo.triggered.connect(
            self.executar_caminho_minimo)

        self.acao_componentes = QAction("Componentes Conexas", self)
        self.acao_componentes.triggered.connect(
            self.executar_componentes_conexas)

        # self.arvore_geradora = QAction("Árvore Geradora", self)
        # self.arvore_geradora.triggered.connect(self.executar_arvore_geradora)

        self.acao_limpar_destaques = QAction("Limpar Cores/Destaques", self)
        self.acao_limpar_destaques.triggered.connect(
            self.cena.limpar_destaques_algoritmos)

        self.acao_selecionar_tudo = QAction("Selecionar Tudo", self)
        self.acao_selecionar_tudo.setShortcut("Ctrl+A")
        self.acao_selecionar_tudo.triggered.connect(self.cena.selecionar_tudo)

        self.acao_caminho_hamiltoniano = QAction(
            "Caminho Hamiltoniano", self)
        self.acao_caminho_hamiltoniano.triggered.connect(
            self.cena.destacar_caminho_hamiltoniano
        )

        self.acao_pontes = QAction("Pontes", self)
        self.acao_pontes.triggered.connect(self.executar_pontes)

        self.acao_arvore_geradora = QAction("Árvore(s) Geradora(s)", self)
        self.acao_arvore_geradora.triggered.connect(
            self.executar_arvore_geradora)

        self.acao_sobre = QAction("&Sobre", self)
        self.acao_sobre.triggered.connect(self.mostrar_sobre)

    def _criar_menus(self) -> None:
        barra_menu = self.menuBar()

        menu_arquivo = barra_menu.addMenu("&Arquivo")
        menu_arquivo.addAction(self.acao_novo)
        menu_arquivo.addAction(self.acao_abrir)
        menu_arquivo.addAction(self.acao_salvar)
        menu_arquivo.addAction(self.acao_salvar)
        menu_arquivo.addSeparator()
        menu_arquivo.addAction(self.acao_salvar_csv)
        menu_arquivo.addAction(self.acao_exportar_png)
        menu_arquivo.addSeparator()
        menu_arquivo.addAction(self.acao_sair)

        menu_editar = barra_menu.addMenu("&Editar")
        menu_editar.addAction(self.acao_selecionar_tudo)
        menu_editar.addAction(self.acao_excluir)
        menu_editar.addSeparator()
        menu_editar.addAction(self.acao_modo_aresta)

        menu_algoritmos = barra_menu.addMenu("Algorit&mos")
        menu_algoritmos.addAction(self.acao_caminho_hamiltoniano)
        menu_algoritmos.addAction(self.acao_caminho_minimo)
        menu_algoritmos.addAction(self.acao_componentes)
        menu_algoritmos.addAction(self.acao_pontes)
        menu_algoritmos.addAction(self.acao_arvore_geradora)
        menu_algoritmos.addSeparator()
        menu_algoritmos.addAction(self.acao_limpar_destaques)

        self.gerenciador_grafos = GerenciadorGrafosPredefinidos(
            self, self.cena)
        self.gerenciador_grafos.instalar_no_menubar(barra_menu)

        self.menu_layout = QMenu("&Layout", self)
        for nome in LAYOUTS:
            acao = QAction(nome, self)
            acao.triggered.connect(
                lambda checked=False, n=nome: self.cena.aplicar_layout(n))
            self.menu_layout.addAction(acao)
        barra_menu.addMenu(self.menu_layout)

        menu_ajuda = barra_menu.addMenu("A&juda")
        menu_ajuda.addAction(self.acao_sobre)

    def _criar_toolbar(self) -> None:
        toolbar = QToolBar("Ferramentas Principais", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # toolbar.addAction(self.acao_novo)
        # toolbar.addAction(self.acao_abrir)
        # toolbar.addAction(self.acao_salvar)
        # toolbar.addSeparator()
        toolbar.addAction(self.acao_modo_aresta)
        # toolbar.addAction(self.acao_excluir)
        toolbar.addSeparator()
        # toolbar.addAction(self.acao_caminho_minimo)
        toolbar.addAction(self.acao_componentes)
        toolbar.addAction(self.acao_pontes)
        toolbar.addAction(self.acao_limpar_destaques)

        # toolbar.addSeparator()
        # btn_layout = QToolButton(toolbar)
        # btn_layout.setText("Layout")
        # btn_layout.setToolTip(
        #     "Reorganizar os vértices com um layout automático")
        # btn_layout.setMenu(self.menu_layout)
        # btn_layout.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        # toolbar.addWidget(btn_layout)

    def _criar_statusbar(self) -> None:
        self.label_modo = QLabel(" MODO: VÉRTICE ")
        self.label_modo.setStyleSheet(
            "background-color: #0066cc; color: white; font-weight: bold; padding: 2px 8px; border-radius: 3px;"
        )
        # self.label_author = QLabel("by Thiago de Melo")
        self.label_author = QLabel(f"by {info_app.AUTOR}")
        # self.statusBar().addPermanentWidget(self.label_author)
        self.statusBar().addPermanentWidget(self.label_modo)
        self.statusBar().showMessage(
            "Clique para adicionar vértices | Arraste vértices/arestas | Tecla E: Modo Aresta | Del: Excluir Seleção"
        )

    # =========================================================================
    # 2. PAINEL LATERAL DE ANÁLISE E MATRIZES
    # =========================================================================

    def _criar_painel_analise(self) -> QWidget:
        container = QWidget(self)
        container.setMinimumWidth(260)
        layout_principal = QVBoxLayout(container)
        layout_principal.setContentsMargins(4, 4, 4, 4)

        abas = QTabWidget(container)

        # --- ABA 1: PROPRIEDADES E GRAUS ---
        widget_props = QWidget()
        layout_props = QVBoxLayout(widget_props)

        layout_props.addWidget(QLabel("<b>Propriedades Gerais</b>"))

        self.tabela_metricas = QTableWidget(0, 2)
        self.tabela_metricas.setHorizontalHeaderLabels(
            ["Propriedade", "Valor"])
        self.tabela_metricas.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.tabela_metricas.horizontalHeader().setStretchLastSection(True)
        self.tabela_metricas.setColumnWidth(0, 190)
        self.tabela_metricas.verticalHeader().setVisible(False)
        self.tabela_metricas.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        layout_props.addWidget(self.tabela_metricas)

        layout_props.addWidget(QLabel("<b>Grau por Vértice</b>"))

        self.tabela_graus = QTableWidget(0, 3)
        self.tabela_graus.setHorizontalHeaderLabels(
            ["Vértice", "Grau", "Vizinhos"])
        self.tabela_graus.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive)
        self.tabela_graus.horizontalHeader().setStretchLastSection(True)
        self.tabela_graus.setColumnWidth(0, 65)
        self.tabela_graus.setColumnWidth(1, 55)
        self.tabela_graus.verticalHeader().setVisible(False)
        self.tabela_graus.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        layout_props.addWidget(self.tabela_graus)

        abas.addTab(widget_props, "Propriedades")

        # --- ABA 2: MATRIZES ---
        widget_matrizes = QWidget()
        layout_matrizes = QVBoxLayout(widget_matrizes)

        linha_topo_load_matrizes = QHBoxLayout()
        self.btn_load_matrizes = QPushButton("De um arquivo")
        self.btn_load_matrizes.clicked.connect(self.carregar_matriz_de_arquivo)
        linha_topo_load_matrizes.addWidget(self.btn_load_matrizes)
        layout_matrizes.addLayout(linha_topo_load_matrizes)

        self.matriz_manual = QTextEdit()
        self.matriz_manual.setFixedHeight(120)
        self.matriz_manual.setAcceptRichText(False)  # evita colar formatação
        self.matriz_manual.setFont(
            QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.matriz_manual.setPlaceholderText(
            "Digite a matriz de adjacência, separando valores por espaços e "
            "linhas por quebras de linha. Por exemplo:\n0 1 0\n1 0 1\n0 1 0")
        layout_matrizes.addWidget(self.matriz_manual)

        self.btn_criar_da_matriz = QPushButton(
            "Criar grafo a partir da matriz")
        self.btn_criar_da_matriz.clicked.connect(self.criar_grafo_da_matriz)
        layout_matrizes.addWidget(self.btn_criar_da_matriz)
        layout_matrizes.addSpacing(8)

        linha_topo_mat = QHBoxLayout()
        self.combo_matriz = QComboBox()
        self.combo_matriz.addItems([
            "Matriz de Adjacência (A)",
            "Matriz de Incidência (B)",
            "Matriz Laplaciana (L = D - A)",
        ])
        self.combo_matriz.currentIndexChanged.connect(
            self._atualizar_tabela_matriz)
        linha_topo_mat.addWidget(self.combo_matriz)

        btn_copiar_mat = QPushButton("Copiar")
        btn_copiar_mat.clicked.connect(self._copiar_matriz_clipboard)
        linha_topo_mat.addWidget(btn_copiar_mat)

        layout_matrizes.addLayout(linha_topo_mat)

        self.tabela_matriz = QTableWidget(0, 0)
        self.tabela_matriz.horizontalHeader().setDefaultSectionSize(38)
        self.tabela_matriz.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection)
        self.tabela_matriz.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabela_matriz.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        layout_matrizes.addWidget(self.tabela_matriz)

        abas.addTab(widget_matrizes, "Matrizes")

        layout_principal.addWidget(abas)
        return container

    def atualizar_painel_analise(self) -> None:
        metricas = self.modelo.calcular_todas_metricas()
        self.tabela_metricas.setRowCount(len(metricas))
        for linha, (nome, valor) in enumerate(metricas):
            self.tabela_metricas.setItem(linha, 0, QTableWidgetItem(nome))
            item_val = QTableWidgetItem(valor)
            item_val.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela_metricas.setItem(linha, 1, item_val)

        nos = self.modelo.vertices_ordenados()
        self.tabela_graus.setRowCount(len(nos))
        for linha, vid in enumerate(nos):
            grau = self.modelo.grafo.degree(vid)
            vizinhos = sorted(self.modelo.grafo.neighbors(vid))
            vizinhos_str = ", ".join(map(str, vizinhos)) if vizinhos else "-"

            item_id = QTableWidgetItem(str(vid))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_grau = QTableWidgetItem(str(grau))
            item_grau.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.tabela_graus.setItem(linha, 0, item_id)
            self.tabela_graus.setItem(linha, 1, item_grau)
            self.tabela_graus.setItem(linha, 2, QTableWidgetItem(vizinhos_str))

        self._atualizar_tabela_matriz()

    def _atualizar_tabela_matriz(self) -> None:
        idx = self.combo_matriz.currentIndex()

        if idx == 0:
            nos, mat = self.modelo.obter_matriz_adjacencia()
            cab_linhas = [str(v) for v in nos]
            cab_colunas = [str(v) for v in nos]
        elif idx == 1:
            nos, arestas, mat = self.modelo.obter_matriz_incidencia()
            cab_linhas = [str(v) for v in nos]
            cab_colunas = [f"{{{u},{v}}}" for u, v in arestas]
        else:
            nos, mat = self.modelo.obter_matriz_laplaciana()
            cab_linhas = [str(v) for v in nos]
            cab_colunas = [str(v) for v in nos]

        linhas, colunas = mat.shape
        self.tabela_matriz.setRowCount(linhas)
        self.tabela_matriz.setColumnCount(colunas)
        self.tabela_matriz.setVerticalHeaderLabels(cab_linhas)
        self.tabela_matriz.setHorizontalHeaderLabels(cab_colunas)

        for r in range(linhas):
            for c in range(colunas):
                val = int(mat[r, c])
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if val != 0:
                    item.setBackground(QColor("#e8f2ff"))
                self.tabela_matriz.setItem(r, c, item)

        nos = sorted(self.modelo.grafo.nodes())
        n = len(nos)
        self._nos_matriz = nos  # Guarda o mapeamento índice da linha/coluna -> ID real do vértice

        # # self.tabela_adjacencia.blockSignals(True)
        # try:
        #     self.tabela_adjacencia.setRowCount(n)
        #     self.tabela_adjacencia.setColumnCount(n)

        #     labels = [str(v) for v in nos]
        #     self.tabela_adjacencia.setHorizontalHeaderLabels(labels)
        #     self.tabela_adjacencia.setVerticalHeaderLabels(labels)

        #     for i, u in enumerate(nos):
        #         for j, v in enumerate(nos):
        #             valor = "1" if self.modelo.grafo.has_edge(u, v) else "0"
        #             item = QTableWidgetItem(valor)
        #             item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        #             if i == j:
        #                 # Diagonal principal não é editável em grafo simples
        #                 item.setFlags(item.flags() & ~
        #                               Qt.ItemFlag.ItemIsEditable)
        #             else:
        #                 item.setFlags(
        #                     item.flags() | Qt.ItemFlag.ItemIsEditable)

        #             self.tabela_adjacencia.setItem(i, j, item)
        # finally:
        #     self.tabela_adjacencia.blockSignals(False)

    def _copiar_matriz_clipboard(self) -> None:
        linhas = self.tabela_matriz.rowCount()
        colunas = self.tabela_matriz.columnCount()
        if linhas == 0 or colunas == 0:
            return

        texto_linhas: List[str] = []
        for r in range(linhas):
            vals = [self.tabela_matriz.item(r, c).text()
                    for c in range(colunas)]
            texto_linhas.append(" ".join(vals))

        QApplication.clipboard().setText("\n".join(texto_linhas))
        self.statusBar().showMessage("Matriz copiada para a área de transferência!", 3000)

    def criar_grafo_da_matriz(self) -> None:
        try:
            matriz = parsear_texto_matriz(self.matriz_manual.toPlainText())
        except ValueError as exc:
            QMessageBox.warning(self, "Matriz inválida", str(exc))
            return

        n = matriz.shape[0]
        if n > LIMITE_VERTICES_MATRIZ:
            QMessageBox.warning(
                self, "Matriz grande demais",
                f"O limite é {LIMITE_VERTICES_MATRIZ} vértices (a matriz tem {n}).")
            return

        if self.modelo.grafo.number_of_nodes() > 0:
            resp = QMessageBox.question(
                self, "Criar grafo",
                "Substituir o grafo atual pelo grafo da matriz? "
                "Alterações não salvas serão perdidas.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resp != QMessageBox.StandardButton.Yes:
                return

        grafo, pos_nx = self.modelo.carregar_de_matriz_adjacencia(matriz)
        pos_pixels = normalizar_layout(
            pos_nx,
            largura=float(max(400, self.cena.width())),
            altura=float(max(300, self.cena.height())))
        self.modelo.substituir_grafo(grafo, pos_pixels)
        self.cena.reconstruir_do_modelo()

        # O grafo agora não corresponde a nenhum arquivo salvo
        self._arquivo_atual = ""
        # self.setWindowTitle("myGraphDrawer — Editor e Analisador de Grafos")
        self._atualizar_titulo()

        # Avisa o que foi ajustado silenciosamente pelo modelo
        avisos = []
        if np.any(np.diag(matriz) != 0):
            avisos.append("diagonal ignorada")
        if not np.array_equal(matriz, matriz.T):
            avisos.append(
                "matriz assimétrica (aresta criada se houver valor em qualquer sentido)")
        if np.any(matriz > 1):
            avisos.append("valores maiores que 1 tratados como 1")
        msg = (f"Grafo criado a partir da matriz ({grafo.number_of_nodes()} vértices, "
               f"{grafo.number_of_edges()} arestas).")
        if avisos:
            msg += " Obs.: " + "; ".join(avisos) + "."
        self.statusBar().showMessage(msg, 10000)

    def carregar_matriz_de_arquivo(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self, "Abrir matriz de adjacência", "",
            "Texto (*.txt *.csv *.tsv);;Todos os arquivos (*)")
        if not caminho:
            return
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                self.matriz_manual.setPlainText(f.read())
        except (OSError, UnicodeDecodeError) as exc:
            QMessageBox.warning(self, "Erro ao abrir arquivo", str(exc))

    # =========================================================================
    # 3. ALGORITMOS VISUAIS
    # =========================================================================

    def executar_caminho_minimo(self) -> None:
        nos = self.modelo.vertices_ordenados()
        if len(nos) < 2:
            QMessageBox.information(
                self, "Caminho Mínimo", "Crie pelo menos 2 vértices no grafo.")
            return

        opcoes = [str(v) for v in nos]
        selecionados = self.cena.obter_vertices_selecionados()
        idx_origem = opcoes.index(str(selecionados[0])) if len(
            selecionados) >= 1 else 0
        idx_destino = min(1, len(opcoes) - 1) if idx_origem == 0 else 0

        # Cria o diálogo único com Origem e Destino
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Caminho Mínimo")
        dialogo.setMinimumWidth(260)

        layout = QFormLayout(dialogo)

        combo_origem = QComboBox(dialogo)
        combo_origem.addItems(opcoes)
        combo_origem.setCurrentIndex(idx_origem)

        combo_destino = QComboBox(dialogo)
        combo_destino.addItems(opcoes)
        combo_destino.setCurrentIndex(idx_destino)

        layout.addRow("Vértice de Origem:", combo_origem)
        layout.addRow("Vértice de Destino:", combo_destino)

        botoes = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dialogo,
        )
        botoes.accepted.connect(dialogo.accept)
        botoes.rejected.connect(dialogo.reject)
        layout.addRow(botoes)

        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        u = int(combo_origem.currentText())
        v = int(combo_destino.currentText())
        caminho = self.modelo.calcular_caminho_minimo(u, v)

        if caminho is None:
            self.cena.limpar_destaques_algoritmos()
            QMessageBox.warning(
                self, "Caminho Mínimo", f"Não existe caminho entre os vértices {u} e {v}.")
        else:
            self.cena.destacar_caminho_minimo(caminho)
            seq_str = " → ".join(map(str, caminho))
            self.statusBar().showMessage(
                f"Caminho mínimo ({u} até {v}): {seq_str} (comprimento: {len(caminho) - 1})"
            )

    def executar_componentes_conexas(self) -> None:
        componentes = self.modelo.obter_componentes_conexas()
        if not componentes:
            return
        self.cena.destacar_componentes_conexas(componentes)
        self.statusBar().showMessage(
            f"Exibindo {len(componentes)} componente(s) conexa(s).")

    def executar_pontes(self) -> None:
        pontes = self.modelo.obter_pontes()
        self.cena.destacar_pontes(pontes)
        if not pontes:
            self.statusBar().showMessage("O grafo não possui pontes.", 4000)
            return
        lista = ", ".join(f"{u}–{v}" for u, v in pontes[:8])
        if len(pontes) > 8:
            lista += ", ..."
        self.statusBar().showMessage(
            f"{len(pontes)} ponte(s) encontrada(s): {lista}", 6000)

    def executar_arvore_geradora(self) -> None:
        arvore = self.modelo.obter_arvore_geradora()
        if arvore is None:
            QMessageBox.information(
                self, "Árvore Geradora", "Não foi possível detectar uma árvore geradora.")
            return
        self.cena.destacar_arvore_geradora(arvore)
        self.statusBar().showMessage(
            f"Árvore(s) geradora(s) destacada(s)."
        )

    # =========================================================================
    # 4. PERSISTÊNCIA (NOVO, ABRIR JSON, SALVAR JSON, EXPORTAR PNG)
    # =========================================================================

    def novo_grafo(self) -> None:
        if self.modelo.grafo.number_of_nodes() > 0:
            resp = QMessageBox.question(
                self,
                "Novo Grafo",
                "Deseja limpar o grafo atual? Alterações não salvas serão perdidas.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

        self.cena.limpar_tudo()
        self._arquivo_atual = ""
        # self.setWindowTitle("myGraphDrawer — Editor e Analisador de Grafos")
        self._atualizar_titulo()
        self.statusBar().showMessage("Novo grafo criado.", 3000)

    def salvar_json(self) -> None:
        if self.modelo.grafo.number_of_nodes() == 0:
            QMessageBox.information(
                self, "Salvar Grafo em JSON", "O grafo está vazio: não há dados para salvar.")
            return

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Grafo em JSON",
            self._arquivo_atual or "grafo.json",
            "Arquivos JSON (*.json)",
        )
        if not caminho:
            return

        if not caminho.endswith(".json"):
            caminho += ".json"

        try:
            self.modelo.salvar_json(caminho)
            self._arquivo_atual = caminho
            # self.setWindowTitle(f"myGraphDrawer — {caminho}")
            self._atualizar_titulo()
            self.statusBar().showMessage(
                f"Grafo salvo com sucesso em: {caminho}", 4000)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao Salvar",
                                 f"Não foi possível salvar o arquivo:\n{exc}")

    def abrir_json(self) -> None:
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir Grafo JSON",
            "",
            "Arquivos JSON (*.json)",
        )
        if not caminho:
            return

        try:
            self.modelo.carregar_json(caminho)
            self.cena.reconstruir_do_modelo()
            self._arquivo_atual = caminho
            # self.setWindowTitle(f"myGraphDrawer — {caminho}")
            self._atualizar_titulo()
            self.statusBar().showMessage(
                f"Grafo carregado de: {caminho}", 4000)
        except Exception as exc:
            QMessageBox.critical(self, "Erro ao Abrir",
                                 f"Arquivo JSON inválido ou corrompido:\n{exc}")

    def salvar_matriz_csv(self) -> None:
        if self.modelo.grafo.number_of_nodes() == 0:
            QMessageBox.information(
                self, "Salvar Matriz", "O grafo está vazio: não há matriz para salvar.")
            return

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Matriz de Adjacência",
            "matriz_adjacencia.csv",
            "Arquivos CSV (*.csv);;Arquivos de texto (*.txt)",
        )
        if not caminho:
            return

        if "." not in caminho.replace("\\", "/").split("/")[-1]:
            caminho += ".csv"

        try:
            self.modelo.salvar_matriz_adjacencia_csv(caminho)
            self.statusBar().showMessage(
                f"Matriz de adjacência salva em: {caminho}", 4000)
        except OSError as exc:
            QMessageBox.critical(self, "Erro ao Salvar",
                                 f"Não foi possível salvar o arquivo:\n{exc}")

    def exportar_png(self) -> None:
        if self.modelo.grafo.number_of_nodes() == 0:
            QMessageBox.information(
                self, "Exportar PNG", "O grafo está vazio: não há imagem para exportar.")
            return

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Imagem PNG",
            "grafo.png",
            "Imagens PNG (*.png)",
        )
        if not caminho:
            return

        if not caminho.endswith(".png"):
            caminho += ".png"

        pixmap = self.cena.grab()
        if pixmap.save(caminho, "PNG"):
            self.statusBar().showMessage(
                f"Imagem exportada para: {caminho}", 4000)
        else:
            QMessageBox.critical(
                self, "Erro", "Falha ao exportar a imagem PNG.")

    # =========================================================================
    # 5. ATUALIZAÇÃO DE STATUS E SINCRONIA DE MODO
    # =========================================================================

    def _ao_alterar_modo(self, modo_aresta_ativo: bool) -> None:
        self.acao_modo_aresta.blockSignals(True)
        self.acao_modo_aresta.setChecked(modo_aresta_ativo)
        self.acao_modo_aresta.blockSignals(False)

        if modo_aresta_ativo:
            self.label_modo.setText(" MODO: ARESTA (E) ")
            self.label_modo.setStyleSheet(
                "background-color: #ff5500; color: white; font-weight: bold; padding: 2px 8px; border-radius: 3px;"
            )
        else:
            self.label_modo.setText(" MODO: PADRÃO ")
            self.label_modo.setStyleSheet(
                "background-color: #0066cc; color: white; font-weight: bold; padding: 2px 8px; border-radius: 3px;"
            )

    def _exibir_mensagem_status(self, texto: str) -> None:
        self.statusBar().showMessage(texto)

    def mostrar_sobre(self) -> None:
        DialogoSobre(self).exec()

    def _atualizar_titulo(self) -> None:
        if self._arquivo_atual:
            self.setWindowTitle(f"{info_app.NOME} — {self._arquivo_atual}")
        else:
            self.setWindowTitle(info_app.TITULO_JANELA)
