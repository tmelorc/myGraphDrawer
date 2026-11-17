from typing import Callable, Dict, Tuple
import networkx as nx

Posicoes = Dict[int, Tuple[float, float]]


def normalizar_layout(
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


def _kamada_kawai(g: nx.Graph) -> Posicoes:
    # Em grafos desconexos o Kamada-Kawai espalha as componentes de forma ruim
    if g.number_of_nodes() > 1 and not nx.is_connected(g):
        return nx.spring_layout(g, seed=42)
    return nx.kamada_kawai_layout(g)


def _planar(g: nx.Graph) -> Posicoes:
    eh_planar, _ = nx.check_planarity(g)
    if not eh_planar:
        raise ValueError("o grafo não é planar.")
    return nx.planar_layout(g)


LAYOUTS: Dict[str, Callable[[nx.Graph], Posicoes]] = {
    "Circular": nx.circular_layout,
    "Força (Spring)": lambda g: nx.spring_layout(g, seed=42),
    "Kamada-Kawai": _kamada_kawai,
    "Planar": _planar,
}
