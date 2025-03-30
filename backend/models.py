from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import uuid

# --- Modelos Base Pydantic ---
# Estes modelos definem a estrutura dos dados usados na aplicação,
# garantindo validação e consistência. Podem ser usados diretamente
# na API ou como base para modelos ORM (SQLAlchemy).

class User(BaseModel):
    """Representa um usuário do sistema."""
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:8]}", description="ID único do usuário.")
    username: str = Field(..., min_length=3, description="Nome de usuário.")
    email: Optional[str] = Field(None, description="Endereço de e-mail (opcional).")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp de criação.")
    # Adicionar outros campos relevantes, como roles, preferências, etc.

class ChatMessage(BaseModel):
    """Representa uma única mensagem na conversa."""
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:8]}", description="ID único da mensagem.")
    session_id: str = Field(..., description="ID da sessão de chat à qual a mensagem pertence.")
    sender_type: Literal["user", "model"] = Field(..., description="Quem enviou a mensagem ('user' ou 'model').")
    sender_id: str = Field(..., description="ID do usuário ou nome/ID do modelo.")
    text: str = Field(..., description="Conteúdo da mensagem.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da mensagem.")
    # Opcional: incluir embedding ou metadados da análise da mensagem
    embedding: Optional[List[float]] = Field(None, description="Embedding vetorial da mensagem.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados adicionais (sentimento, tópicos, etc.).")

class HoTNodeModel(BaseModel):
    """Representa um nó no Hipergrafo de Pensamentos (versão Pydantic)."""
    id: str = Field(..., description="ID único do nó.")
    label: str = Field(..., description="Conteúdo textual do nó (pensamento/mensagem).")
    type: str = Field(default='thought', description="Tipo do nó (e.g., 'thought', 'user_input', 'model_response').")
    timestamp: datetime = Field(..., description="Timestamp de criação do nó.")
    relevance: float = Field(default=0.5, ge=0.0, le=1.0, description="Relevância do nó (ajustável).")
    model_source: Optional[str] = Field(None, description="Modelo GGUF que originou o nó (se aplicável).")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Atributos adicionais.")
    # O embedding pode ser armazenado separadamente ou opcionalmente aqui
    # embedding: Optional[List[float]] = None

class HoTEdgeModel(BaseModel):
    """Representa uma hiperaresta no Hipergrafo de Pensamentos (versão Pydantic)."""
    id: str = Field(..., description="ID único da hiperaresta.")
    nodes: Set[str] = Field(..., min_items=2, description="Conjunto de IDs dos nós conectados.")
    type: str = Field(default='related', description="Tipo da relação (e.g., 'support', 'contrast', 'elaboration').")
    timestamp: datetime = Field(..., description="Timestamp de criação da aresta.")
    weight: float = Field(default=0.5, ge=0.0, le=1.0, description="Peso/Força da conexão (ajustável).")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Atributos adicionais.")

    @validator('nodes')
    def check_min_nodes(cls, v):
        if len(v) < 2:
            raise ValueError('Uma hiperaresta deve conectar pelo menos 2 nós.')
        return v

class HoTStateModel(BaseModel):
    """Representa o estado completo de um Hipergrafo de Pensamentos."""
    session_id: str = Field(..., description="ID da sessão associada a este HoT.")
    nodes: Dict[str, HoTNodeModel] = Field(default_factory=dict, description="Dicionário de nós no grafo.")
    edges: Dict[str, HoTEdgeModel] = Field(default_factory=dict, description="Dicionário de hiperarestas no grafo.")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da última atualização.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadados gerais do HoT.")

class AnalysisResult(BaseModel):
    """Representa o resultado de uma análise específica."""
    analysis_id: str = Field(default_factory=lambda: f"analysis_{uuid.uuid4().hex[:8]}", description="ID único da análise.")
    request_id: Optional[str] = Field(None, description="ID da requisição que originou a análise.")
    analysis_type: str = Field(..., description="Tipo de análise realizada (e.g., 'sentiment', 'topic').")
    input_data_ref: Optional[str] = Field(None, description="Referência aos dados de entrada (e.g., message_id).")
    result: Dict[str, Any] = Field(..., description="Resultado detalhado da análise.")
    model_used: Optional[str] = Field(None, description="Modelo usado na análise.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp da análise.")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confiança do resultado da análise.")

class UserSettings(BaseModel):
    """Representa as configurações de um usuário."""
    user_id: str = Field(..., description="ID do usuário.")
    general: Dict[str, Any] = Field(default_factory=dict, description="Configurações gerais (idioma, tema, etc.).")
    analysis: Dict[str, Any] = Field(default_factory=dict, description="Configurações de análise (modelo padrão, HoT, etc.).")
    security: Dict[str, Any] = Field(default_factory=dict, description="Configurações de segurança (2FA, etc.).")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# --- Exemplo de Uso (Opcional) ---
if __name__ == "__main__":
    try:
        # Criar um nó
        node1_data = {
            "id": "n_1",
            "label": "Primeiro pensamento sobre IA.",
            "type": "thought",
            "timestamp": datetime.now(),
            "relevance": 0.8,
            "model_source": "model_A"
        }
        node1 = HoTNodeModel(**node1_data)
        print("Nó Válido:", node1.dict())

        # Criar uma aresta
        edge1_data = {
            "id": "e_1",
            "nodes": {"n_1", "n_2"}, # Assume que n_2 existe
            "type": "elaboration",
            "timestamp": datetime.now(),
            "weight": 0.7
        }
        edge1 = HoTEdgeModel(**edge1_data)
        print("\nAresta Válida:", edge1.dict())

        # Tentar criar aresta inválida
        try:
            HoTEdgeModel(id="e_invalid", nodes={"n_1"}, timestamp=datetime.now())
        except ValueError as e:
            print(f"\nErro esperado ao criar aresta inválida: {e}")

        # Criar estado HoT
        hot_state = HoTStateModel(session_id="session_123", nodes={"n_1": node1}, edges={"e_1": edge1})
        print("\nEstado HoT Válido:", hot_state.dict(exclude={'nodes', 'edges'})) # Exclui nós/arestas para brevidade

    except ValidationError as e:
        print("\nErro de Validação Pydantic:")
        print(e.json())
