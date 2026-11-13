import json
from typing import Any, Callable, Dict, List, Optional, Tuple
import networkx as nx
import numpy as np


# Registro global de métricas para facilitar extensões futuras
_METRICAS_REGISTRADAS: List[Tuple[str, Callable[["ModeloGrafo"], Any]]] = []


def registrar_metrica(nome_exibicao: str):
    """
    Decorador que registra automaticamente uma propriedade ou algoritmo
    para ser exibido no painel de análise da interface.
    """
    def decorator(func: Callable[["ModeloGrafo"], Any]):
        _METRICAS_REGISTRADAS.append((nome_exibicao, func))
        return func
    return decorator


class ModeloGrafo:
    """
    Gerencia a representação matemática do grafo simples não-direcionado (NetworkX),
    controle de IDs incrementais (Opção B), matrizes e persistência em JSON.
    """

    def __init__(self) -> None:
        self.grafo: nx.Graph = nx.Graph()
        self._proximo_id: int = 0
        # Armazena coordenadas visuais {id_vertice: (x, y)} para sincronia e JSON
        self.posicoes: Dict[int, Tuple[float, float]] = {}

    # =========================================================================
    # 1. MANIPULAÇÃO DE VÉRTICES E ARESTAS (REGRAS DE GRAFO SIMPLES)
    # =========================================================================

    def limpar(self) -> None:
        """Reseta completamente o grafo e o contador de IDs."""
        self.grafo.clear()
        self.posicoes.clear()
        self._proximo_id = 0

    def adicionar_vertice(self, x: float, y: float, vertice_id: Optional[int] = None) -> int:
        """
        Adiciona um vértice ao grafo com ID incremental fixo (Opção B).
        Se vertice_id for informado (ex: ao carregar JSON), utiliza-o e ajusta o contador.
        """
        if vertice_id is None:
            vid = self._proximo_id
            self._proximo_id += 1
        else:
            vid = int(vertice_id)
            if vid >= self._proximo_id:
                self._proximo_id = vid + 1

        self.grafo.add_node(vid)
        self.posicoes[vid] = (float(x), float(y))
        return vid

    def atualizar_posicao(self, vid: int, x: float, y: float) -> None:
        """Atualiza as coordenadas visuais armazenadas de um vértice."""
        if vid in self.posicoes:
            self.posicoes[vid] = (float(x), float(y))

    def remover_vertice(self, vid: int) -> bool:
        """Remove o vértice e suas arestas incidentes sem renumerar os demais."""
        if vid in self.grafo:
            self.grafo.remove_node(vid)
            self.posicoes.pop(vid, None)
            return True
        return False

    def adicionar_aresta(self, u: int, v: int) -> bool:
        """
        Adiciona uma aresta não-direcionada {u, v}.
        Bloqueia laços (u == v) e arestas múltiplas (já existentes).
        Retorna True se a aresta foi criada, False caso contrário.
        """
        if u == v:
            return False  # Bloqueia laço (self-loop)
        if u not in self.grafo or v not in self.grafo:
            return False
        if self.grafo.has_edge(u, v):
            return False  # Bloqueia aresta paralela

        self.grafo.add_edge(u, v)
        return True

    def remover_aresta(self, u: int, v: int) -> bool:
        """Remove a aresta entre u e v, se existir."""
        if self.grafo.has_edge(u, v):
            self.grafo.remove_edge(u, v)
            return True
        return False

    def vertices_ordenados(self) -> List[int]:
        """Retorna a lista de IDs dos vértices ativos em ordem crescente."""
        return sorted(self.grafo.nodes())

    # =========================================================================
    # 2. MATRIZES DO GRAFO (ADJACÊNCIA, INCIDÊNCIA E LAPLACIANA)
    # =========================================================================

    def obter_matriz_adjacencia(self) -> Tuple[List[int], np.ndarray]:
        """Retorna (lista_ids_ordenados, matriz_adjacencia_numpy)."""
        nos = self.vertices_ordenados()
        if not nos:
            return [], np.zeros((0, 0), dtype=int)
        mat = nx.to_numpy_array(self.grafo, nodelist=nos, dtype=int)
        return nos, mat

    def obter_matriz_incidencia(self) -> Tuple[List[int], List[Tuple[int, int]], np.ndarray]:
        """
        Retorna (lista_ids_ordenados, lista_arestas_ordenadas, matriz_incidencia_numpy).
        Cada linha corresponde a um vértice e cada coluna a uma aresta.
        """
        nos = self.vertices_ordenados()
        arestas = sorted(tuple(sorted(e)) for e in self.grafo.edges())
        if not nos or not arestas:
            return nos, arestas, np.zeros((len(nos), len(arestas)), dtype=int)

        # incidence_matrix retorna matriz esparsa com floats; convertemos para int denso
        mat_esparsa = nx.incidence_matrix(
            self.grafo, nodelist=nos, edgelist=arestas, oriented=False)
        mat = mat_esparsa.toarray().astype(int)
        return nos, arestas, mat

    def obter_matriz_laplaciana(self) -> Tuple[List[int], np.ndarray]:
        """Retorna (lista_ids_ordenados, matriz_laplaciana_L = D - A)."""
        nos = self.vertices_ordenados()
        if not nos:
            return [], np.zeros((0, 0), dtype=int)
        mat_esparsa = nx.laplacian_matrix(self.grafo, nodelist=nos)
        mat = mat_esparsa.toarray().astype(int)
        return nos, mat

    # =========================================================================
    # 3. ALGORITMOS VISUAIS AUXILIARES
    # =========================================================================

    def calcular_caminho_minimo(self, origem: int, destino: int) -> Optional[List[int]]:
        """Retorna a sequência de vértices do menor caminho entre origem e destino, ou None."""
        if origem not in self.grafo or destino not in self.grafo:
            return None
        try:
            return nx.shortest_path(self.grafo, source=origem, target=destino)
        except nx.NetworkXNoPath:
            return None

    def obter_componentes_conexos(self) -> List[List[int]]:
        """Retorna lista de listas com os IDs de cada componente conexo."""
        return [sorted(list(comp)) for comp in nx.connected_components(self.grafo)]

    # =========================================================================
    # 4. MÉTRICAS EXTENSÍVEIS (PAINEL LATERAL)
    # =========================================================================

    def calcular_todas_metricas(self) -> List[Tuple[str, str]]:
        """Executa todas as métricas registradas e retorna pares (Nome, Valor Formatado)."""
        resultados: List[Tuple[str, str]] = []
        for nome, func in _METRICAS_REGISTRADAS:
            try:
                valor = func(self)
                resultados.append((nome, str(valor)))
            except Exception as exc:
                resultados.append((nome, f"Erro: {exc}"))
        return resultados

    @registrar_metrica("Ordem |V| (Vértices)")
    def metrica_ordem(self) -> int:
        return self.grafo.number_of_nodes()

    @registrar_metrica("Tamanho |E| (Arestas)")
    def metrica_tamanho(self) -> int:
        return self.grafo.number_of_edges()

    @registrar_metrica("Grau Mínimo (δ)")
    def metrica_grau_min(self) -> str:
        if self.grafo.number_of_nodes() == 0:
            return "-"
        return str(min(d for _, d in self.grafo.degree()))

    @registrar_metrica("Grau Máximo (Δ)")
    def metrica_grau_max(self) -> str:
        if self.grafo.number_of_nodes() == 0:
            return "-"
        return str(max(d for _, d in self.grafo.degree()))

    @registrar_metrica("Grau Médio")
    def metrica_grau_medio(self) -> str:
        n = self.grafo.number_of_nodes()
        if n == 0:
            return "-"
        media = (2 * self.grafo.number_of_edges()) / n
        return f"{media:.2f}"

    @registrar_metrica("Conexo")
    def metrica_conexo(self) -> str:
        if self.grafo.number_of_nodes() == 0:
            return "Vazio"
        return "Sim" if nx.is_connected(self.grafo) else "Não"

    @registrar_metrica("Componentes Conexos")
    def metrica_num_componentes(self) -> int:
        if self.grafo.number_of_nodes() == 0:
            return 0
        return nx.number_connected_components(self.grafo)

    @registrar_metrica("É Árvore?")
    def metrica_arvore(self) -> str:
        if self.grafo.number_of_nodes() == 0:
            return "Não"
        return "Sim" if nx.is_tree(self.grafo) else "Não"

    @registrar_metrica("É Bipartido?")
    def metrica_bipartido(self) -> str:
        if self.grafo.number_of_nodes() == 0:
            return "Sim"
        return "Sim" if nx.is_bipartite(self.grafo) else "Não"

    @registrar_metrica("Planar")
    def metrica_planar(self) -> str:
        if self.grafo.number_of_nodes() < 5:
            return "Sim"
        eh_planar, _ = nx.check_planarity(self.grafo)
        return "Sim" if eh_planar else "Não"

    # =========================================================================
    # 5. PERSISTÊNCIA EM JSON (SALVAR E ABRIR)
    # =========================================================================

    def salvar_json(self, caminho_arquivo: str) -> None:
        """Exporta a topologia e as posições visuais dos vértices para JSON."""
        dados = {
            "aplicacao": "myGraphDrawer",
            "tipo": "nao_direcionado",
            "proximo_id": self._proximo_id,
            "vertices": [
                {
                    "id": vid,
                    "x": self.posicoes[vid][0],
                    "y": self.posicoes[vid][1],
                }
                for vid in self.vertices_ordenados()
            ],
            "arestas": [
                {"origem": int(u), "destino": int(v)}
                for u, v in sorted(tuple(sorted(e)) for e in self.grafo.edges())
            ],
        }
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)

    def carregar_json(self, caminho_arquivo: str) -> None:
        """Lê um arquivo JSON e reconstrói o grafo e suas coordenadas."""
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)

        self.limpar()

        for v in dados.get("vertices", []):
            self.adicionar_vertice(
                x=float(v["x"]),
                y=float(v["y"]),
                vertice_id=int(v["id"]),
            )

        for a in dados.get("arestas", []):
            self.adicionar_aresta(int(a["origem"]), int(a["destino"]))

        # Garante que o contador respeite o maior ID salvo ou o valor explícito
        if "proximo_id" in dados:
            self._proximo_id = max(self._proximo_id, int(dados["proximo_id"]))
