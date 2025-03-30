import logging
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from threading import Lock
from datetime import datetime
import networkx as nx # Using NetworkX for graph metrics as a proxy/helper
import numpy as np

# Importar outros serviços ou utils se necessário
# from .gguf_service import get_gguf_service # Exemplo: para obter embeddings
# from backend.utils.logging_config import get_logger # Usar o logger configurado

# Configuração básica de logging se o avançado não estiver pronto
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hot_service")

# --- Estruturas de Dados (Podem ser movidas para models.py depois) ---

class HoTNode:
    """Representa um nó no Hipergrafo de Pensamentos."""
    def __init__(self, node_id: str, label: str, node_type: str = 'thought',
                 timestamp: Optional[datetime] = None, relevance: float = 0.5,
                 model_source: Optional[str] = None, **kwargs):
        self.id = node_id
        self.label = label # O texto do pensamento/mensagem
        self.type = node_type # 'thought', 'user_input', 'model_response', etc.
        self.timestamp = timestamp or datetime.now()
        self.relevance = relevance # Relevância ajustável pelo usuário/sistema
        self.model_source = model_source # Qual modelo gerou (se aplicável)
        self.embedding: Optional[np.ndarray] = None # Vetor de embedding (opcional)
        self.attributes = kwargs # Atributos adicionais

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "relevance": self.relevance,
            "model_source": self.model_source,
            "attributes": self.attributes,
            # Não serializar embedding por padrão para manter JSON leve
        }

class HoTEdge:
    """Representa uma hiperaresta no Hipergrafo de Pensamentos."""
    def __init__(self, edge_id: str, node_ids: Set[str], edge_type: str = 'related',
                 timestamp: Optional[datetime] = None, weight: float = 0.5,
                 **kwargs):
        if len(node_ids) < 2:
            raise ValueError("Uma hiperaresta deve conectar pelo menos 2 nós.")
        self.id = edge_id
        self.nodes = node_ids # Conjunto de IDs dos nós conectados
        self.type = edge_type # 'support', 'contrast', 'elaboration', 'related', etc.
        self.timestamp = timestamp or datetime.now()
        self.weight = weight # Peso/Força da conexão, ajustável pelo usuário/sistema
        self.attributes = kwargs # Atributos adicionais

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nodes": list(self.nodes), # Serializa set como lista
            "type": self.type,
            "timestamp": self.timestamp.isoformat(),
            "weight": self.weight,
            "attributes": self.attributes,
        }

# --- Serviço HoT ---

class HoTService:
    """
    Serviço para gerenciar o estado e as operações do Hipergrafo de Pensamentos (HoT).
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(HoTService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Inicializa o serviço HoT (se ainda não inicializado)."""
        if self._initialized:
            return
        with self._lock:
            if self._initialized:
                return

            logger.info(f"Inicializando HoTService (PID: {os.getpid()})...")
            self.nodes: Dict[str, HoTNode] = {}
            self.edges: Dict[str, HoTEdge] = {}
            self._node_counter = 0
            self._edge_counter = 0
            # self.gguf_service = get_gguf_service() # Obter instância do serviço GGUF
            self._initialized = True
            logger.info("HoTService inicializado.")

    def _generate_id(self, prefix: str) -> str:
        """Gera um ID único para nós ou arestas."""
        timestamp_ms = int(time.time() * 1000)
        if prefix == "node":
            self._node_counter += 1
            return f"n_{timestamp_ms}_{self._node_counter}"
        elif prefix == "edge":
            self._edge_counter += 1
            return f"e_{timestamp_ms}_{self._edge_counter}"
        else:
            raise ValueError("Prefixo de ID inválido.")

    def add_node(self, label: str, node_type: str, model_source: Optional[str] = None, relevance: float = 0.5, **kwargs) -> HoTNode:
        """Adiciona um novo nó ao hipergrafo."""
        node_id = self._generate_id("node")
        node = HoTNode(node_id, label, node_type, model_source=model_source, relevance=relevance, **kwargs)
        # --- Geração de Embedding (Opcional, pode ser custoso) ---
        # try:
        #     if self.gguf_service:
        #         # Assumindo que o serviço GGUF tem um método get_default_model_name()
        #         default_model = self.gguf_service.get_default_model_name() # Ou obter do contexto
        #         if default_model:
        #             node.embedding = self.gguf_service.generate_embedding(default_model, label)
        # except Exception as e:
        #     logger.warning(f"Não foi possível gerar embedding para o nó {node_id}: {e}")
        # --- Fim Geração Embedding ---
        self.nodes[node_id] = node
        logger.info(f"Nó adicionado: ID={node_id}, Tipo={node_type}, Label='{label[:30]}...'")
        return node

    def add_edge(self, node_ids: List[str], edge_type: str = 'related', weight: float = 0.5, **kwargs) -> Optional[HoTEdge]:
        """Adiciona uma nova hiperaresta conectando nós existentes."""
        node_id_set = set(node_ids)
        if len(node_id_set) < 2:
            logger.warning(f"Tentativa de criar hiperaresta com menos de 2 nós únicos: {node_ids}")
            return None
        # Verifica se todos os nós existem
        for node_id in node_id_set:
            if node_id not in self.nodes:
                logger.error(f"Nó '{node_id}' não encontrado ao tentar criar aresta.")
                raise ValueError(f"Nó '{node_id}' não existe no hipergrafo.")

        edge_id = self._generate_id("edge")
        edge = HoTEdge(edge_id, node_id_set, edge_type, weight=weight, **kwargs)
        self.edges[edge_id] = edge
        logger.info(f"Hiperaresta adicionada: ID={edge_id}, Tipo={edge_type}, Nós={node_id_set}")
        return edge

    def update_hot_from_interaction(self, user_message: str, model_response: str, model_name: str) -> Tuple[HoTNode, HoTNode, Optional[HoTEdge]]:
        """
        Atualiza o HoT com base em uma nova interação de chat.
        Adiciona nós para a mensagem do usuário e a resposta do modelo,
        e uma hiperaresta relacionando-os (e potencialmente nós anteriores).
        """
        logger.info(f"Atualizando HoT com nova interação (Modelo: {model_name}).")
        user_node = self.add_node(user_message, node_type='user_input')
        model_node = self.add_node(model_response, node_type='model_response', model_source=model_name)

        # --- Lógica de Conexão (Pode ser mais sofisticada) ---
        # Conectar a nova resposta ao input do usuário e talvez ao último pensamento relevante
        related_nodes = {user_node.id, model_node.id}
        # Exemplo: encontrar último nó relevante no contexto (pode vir do chat history ou HoT)
        # last_relevant_node_id = self._find_last_relevant_node()
        # if last_relevant_node_id:
        #     related_nodes.add(last_relevant_node_id)

        new_edge = None
        if len(related_nodes) >= 2:
            # Calcular peso inicial baseado em similaridade (exemplo)
            initial_weight = 0.6 # Placeholder
            # try:
            #     if user_node.embedding is not None and model_node.embedding is not None:
            #         # Calcular similaridade cosseno
            #         sim = np.dot(user_node.embedding, model_node.embedding) / (np.linalg.norm(user_node.embedding) * np.linalg.norm(model_node.embedding))
            #         initial_weight = float(np.clip(sim, 0, 1))
            # except Exception as e:
            #     logger.warning(f"Não foi possível calcular similaridade para peso da aresta: {e}")

            new_edge = self.add_edge(list(related_nodes), edge_type='response_to', weight=initial_weight)
        # --- Fim Lógica de Conexão ---

        return user_node, model_node, new_edge

    def adjust_hot_element(self, element_id: str, element_type: str, new_value: float) -> bool:
        """
        Aplica ajustes feitos pelo usuário a um nó (relevância) ou aresta (peso).
        """
        logger.info(f"Ajustando elemento HoT: ID={element_id}, Tipo={element_type}, Novo Valor={new_value}")
        if element_type == 'node':
            if element_id in self.nodes:
                # Valida o valor da relevância
                if 0.0 <= new_value <= 1.0:
                    self.nodes[element_id].relevance = new_value
                    logger.info(f"Relevância do nó {element_id} ajustada para {new_value}")
                    return True
                else:
                    logger.warning(f"Valor de relevância inválido ({new_value}) para o nó {element_id}. Deve ser entre 0 e 1.")
                    return False
            else:
                logger.warning(f"Nó {element_id} não encontrado para ajuste.")
                return False
        elif element_type == 'edge':
            if element_id in self.edges:
                 # Valida o valor do peso
                if 0.0 <= new_value <= 1.0:
                    self.edges[element_id].weight = new_value
                    logger.info(f"Peso da aresta {element_id} ajustado para {new_value}")
                    return True
                else:
                    logger.warning(f"Valor de peso inválido ({new_value}) para a aresta {element_id}. Deve ser entre 0 e 1.")
                    return False
            else:
                logger.warning(f"Aresta {element_id} não encontrada para ajuste.")
                return False
        else:
            logger.warning(f"Tipo de elemento inválido para ajuste: {element_type}")
            return False

    def get_current_hot_data(self) -> Dict[str, Any]:
        """Retorna a representação atual do HoT para visualização."""
        # Simplificação para D3: converter para nós e links simples
        # Uma visualização real de hipergrafo precisaria de mais dados
        nodes_for_viz = [n.to_dict() for n in self.nodes.values()]
        edges_for_viz = [e.to_dict() for e in self.edges.values()]

        # Adicionar posições (calculadas no frontend ou aqui se usar layout backend)
        # Exemplo simples de posições aleatórias se não houver layout
        for node in nodes_for_viz:
            if 'position' not in node:
                 node['position'] = [np.random.rand() * 500 - 250, np.random.rand() * 400 - 200] # Posições aleatórias

        return {
            "nodes": nodes_for_viz,
            "edges": edges_for_viz, # O frontend precisará interpretar isso como hiperarestas
            "metadata": {"last_updated": datetime.now().isoformat()}
        }

    def calculate_hot_metrics(self) -> Dict[str, Any]:
        """Calcula métricas básicas sobre o estado atual do HoT."""
        num_nodes = len(self.nodes)
        num_edges = len(self.edges)
        avg_edge_size = np.mean([len(e.nodes) for e in self.edges.values()]) if num_edges > 0 else 0
        avg_node_degree = np.mean([sum(1 for e in self.edges.values() if n_id in e.nodes) for n_id in self.nodes]) if num_nodes > 0 else 0

        # Usar NetworkX para métricas mais complexas (como densidade, centralidade)
        # Convertendo hipergrafo para grafo simples para métricas aproximadas
        G = nx.Graph()
        if num_nodes > 0:
            G.add_nodes_from(self.nodes.keys())
            for edge in self.edges.values():
                # Adiciona arestas entre todos os pares de nós na hiperaresta
                from itertools import combinations
                for u, v in combinations(edge.nodes, 2):
                    if G.has_edge(u, v):
                        G[u][v]['weight'] += edge.weight # Acumula peso se já existir
                    else:
                        G.add_edge(u, v, weight=edge.weight)

        density = nx.density(G) if num_nodes > 1 else 0
        avg_centrality = np.mean(list(nx.degree_centrality(G).values())) if num_nodes > 0 else 0

        return {
            "node_count": num_nodes,
            "edge_count": num_edges,
            "avg_hyperedge_size": avg_edge_size,
            "avg_node_degree": avg_node_degree, # Grau no hipergrafo
            "graph_density": density, # Densidade do grafo simples derivado
            "avg_graph_centrality": avg_centrality # Centralidade no grafo simples derivado
        }

    def generate_hot_insights(self) -> List[str]:
        """Gera insights textuais básicos sobre o HoT."""
        metrics = self.calculate_hot_metrics()
        insights = []
        if metrics["node_count"] > 50:
            insights.append("O grafo de pensamentos está se tornando complexo, indicando uma exploração profunda.")
        if metrics["graph_density"] > 0.5:
            insights.append("Alta densidade no grafo sugere forte interconexão entre os pensamentos.")
        if metrics["avg_hyperedge_size"] > 3:
             insights.append("Hiperarestas grandes indicam pensamentos que conectam múltiplos conceitos simultaneamente.")

        # Adicionar mais regras de insights baseadas em métricas
        if not insights:
            insights.append("Nenhum insight significativo gerado no momento.")

        return insights

    def get_hot_context_for_prompt(self, max_nodes: int = 5, max_tokens: int = 500) -> str:
        """
        Extrai contexto relevante do HoT para adicionar ao próximo prompt do GGUF.
        Prioriza nós mais recentes e/ou mais relevantes.
        """
        if not self.nodes:
            return ""

        # Ordenar nós por timestamp (mais recentes primeiro) ou relevância
        # Exemplo: por timestamp
        sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.timestamp, reverse=True)
        # Exemplo: por relevância
        # sorted_nodes = sorted(self.nodes.values(), key=lambda n: n.relevance, reverse=True)

        context_str = "Contexto do Hipergrafo de Pensamentos:\n"
        token_count = 0
        nodes_added = 0

        for node in sorted_nodes:
            node_text = f"- Nó {node.id} ({node.type}, Rel: {node.relevance:.2f}): {node.label}\n"
            node_tokens = len(node_text.split()) # Estimativa simples

            if nodes_added < max_nodes and token_count + node_tokens <= max_tokens:
                context_str += node_text
                token_count += node_tokens
                nodes_added += 1
            else:
                break # Parar se atingir limite de nós ou tokens

        # Adicionar informações sobre arestas recentes/relevantes (opcional e mais complexo)

        logger.debug(f"Contexto HoT gerado: {nodes_added} nós, {token_count} tokens.")
        return context_str.strip()

    def clear_hot(self):
        """Limpa o estado atual do hipergrafo."""
        self.nodes.clear()
        self.edges.clear()
        self._node_counter = 0
        self._edge_counter = 0
        logger.info("Hipergrafo de Pensamentos limpo.")

# --- Singleton Instance ---
hot_service_instance = HoTService()

def get_hot_service() -> HoTService:
    """Função para obter a instância singleton do HoTService."""
    return hot_service_instance
