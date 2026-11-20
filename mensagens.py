from enum import Enum
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

SMALL_TIME = 1500
MED_TIME = 3000
BIG_TIME = 5000


class Mensagem(Enum):

    # Mensagens fixas: (texto, duracao_ms)

    MODO_VERTICE = (
        "Clique para adicionar vértices | Arraste vértices/arestas | Tecla E: Modo Aresta | Del: Excluir Selecionados | ESC: Limpar Seleção", 0)

    MODO_ARESTA = (
        "Clique no vértice inicial e depois em um vértice ou no vazio para criar o vértice final da aresta", 0)

    GRAFO_PLANAR = (
        "O grafo atual é planar (nenhum subgrafo de Kuratowski)", MED_TIME)

    SUBGRAFO_NAO_PLANAR = (
        "Subgrafo não planar destacado (K_5 ou K_{3,3})", MED_TIME)

    NOVO_GRAFO = ("Novo grafo criado", SMALL_TIME)

    SELECAO_LIMPA = ("Seleção limpa", SMALL_TIME)

    # Mensagens com campos variáveis ({placeholders})

    SALVAR_GRAFO = ("Grafo salvo com sucesso em {caminho}", MED_TIME)

    ABRIR_GRAFO = ("Grafo carregado de {caminho}", MED_TIME)

    SALVAR_MAT_ADJ = ("Matriz de adjacência salva em {caminho}", MED_TIME)

    SALVAR_PNG = ("Imagem exportada para {caminho}", MED_TIME)

    # MODO_ARESTA_ATIVO = (
    #     "Modo aresta: clique no vértice de origem e depois no destino.", 0)

    VERTICE_CRIADO = ("Vértice {vid} criado em ({x:.0f}, {y:.0f})", MED_TIME)

    ARESTA_CRIADA = ("Aresta ({u}, {v}) adicionada ao grafo", MED_TIME)

    SELECAO_MULTIPLA = (
        "{qtd_v} vértice(s) e {qtd_a} aresta(s) selecionado(s)", MED_TIME)

    GRAFO_CARREGADO = (
        "Grafo carregado: {n} vértices e {m} arestas", MED_TIME)

    VERTICES_CORTE = (
        "{qtd} vértice(s) de corte encontrado(s): {lista}", BIG_TIME)

    def formatar(self, **kwargs) -> tuple[str, int]:
        """Retorna (texto_formatado, duracao_ms) preenchendo os placeholders."""
        template, duracao = self.value
        return template.format(**kwargs), duracao


class _CanalStatus(QObject):
    nova_mensagem = pyqtSignal(str, int)

    def __init__(self) -> None:
        super().__init__()
        self._mensagem_principal: str = ""
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._exibir_pendente)
        self._pendente: tuple[str, int] | None = None

    def definir_principal(self, texto: str, exibir_agora: bool = True) -> None:
        """Atualiza a mensagem fixa padrão e, opcionalmente, já a exibe."""
        self._mensagem_principal = texto
        if exibir_agora and not self._timer.isActive():
            self.nova_mensagem.emit(self._mensagem_principal, 0)

    def enviar(self, texto: str, duracao: int) -> None:
        # Cancela qualquer mensagem agendada anteriormente para não haver conflito
        self._timer.stop()
        # self._pendente = None
        self.nova_mensagem.emit(texto, duracao)
        # Se for temporária e houver uma mensagem principal definida, agenda o retorno
        if duracao > 0 and self._mensagem_principal:
            self._timer.start(duracao)

    def _restaurar_principal(self) -> None:
        if self._mensagem_principal:
            self.nova_mensagem.emit(self._mensagem_principal, 0)

    def enviar_com_seguinte(
        self,
        texto_inicial: str,
        duracao_inicial: int,
        texto_seguinte: str,
        duracao_seguinte: int = 0,
    ) -> None:
        self._timer.stop()
        self.nova_mensagem.emit(texto_inicial, duracao_inicial)
        self._pendente = (texto_seguinte, duracao_seguinte)
        self._timer.start(duracao_inicial)

    def _exibir_pendente(self) -> None:
        if self._pendente is not None:
            texto, duracao = self._pendente
            self._pendente = None
            self.nova_mensagem.emit(texto, duracao)


# Instância única importável por qualquer arquivo
_canal = _CanalStatus()


def definir_mensagem_principal(msg: Mensagem, *, exibir_agora: bool = True, **kwargs) -> None:
    """Define a mensagem fixa padrão de qualquer lugar do projeto."""
    texto, _ = msg.formatar(**kwargs)
    _canal.definir_principal(texto, exibir_agora=exibir_agora)


def notificar(msg: Mensagem, **kwargs) -> None:
    """Função global: envia a mensagem formatada direto para a statusBar."""
    texto, duracao = msg.formatar(**kwargs)
    _canal.nova_mensagem.emit(texto, duracao)


def notificar_sequencia(
    msg_temporaria: Mensagem,
    msg_fixa: Mensagem,
    *,
    params_temp: dict | None = None,
    params_fixa: dict | None = None,
) -> None:
    """Exibe msg_temporaria pelo tempo dela e, ao expirar, fixa msg_fixa."""
    texto_1, duracao_1 = msg_temporaria.formatar(**(params_temp or {}))
    texto_2, duracao_2 = msg_fixa.formatar(**(params_fixa or {}))
    _canal.enviar_com_seguinte(texto_1, duracao_1, texto_2, duracao_2)


def conectar_status_bar(status_bar) -> None:
    """Conecta o canal global à QStatusBar da JanelaPrincipal uma única vez."""
    _canal.nova_mensagem.connect(status_bar.showMessage)


# exemplo
# # Caso 1: Ambas sem variáveis
# notificar_sequencia(Mensagem.SUBGRAFO_NAO_PLANAR, Mensagem.PRONTO)

# # Caso 2: Com variáveis preenchidas em ambas
# notificar_sequencia(
#     Mensagem.GRAFO_CARREGADO,
#     Mensagem.MODO_EDICAO,
#     params_temp={"n": n, "m": m},
#     params_fixa={"n": n, "m": m},
# )
