import logging
from fastapi import APIRouter, HTTPException, Body, Depends, status
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List

# Importar serviços e logger configurado
# Ajuste os imports conforme a estrutura final do seu projeto
try:
    from backend.services.hot_service import get_hot_service, HoTService
    from backend.utils.logging_config import get_logger # Usar o logger configurado
    logger = get_logger("api.hot")
except ImportError:
    # Fallback básico se a estrutura não estiver totalmente configurada
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("api.hot")
    # Criar classes dummy para evitar erros de importação iniciais
    class HoTService: pass
    def get_hot_service(): return HoTService()

# --- Pydantic Models for Request/Response Validation ---

class HoTAdjustmentRequest(BaseModel):
    """Modelo para a requisição de ajuste de elemento do HoT."""
    element_id: str = Field(..., description="ID do nó ou hiperaresta a ser ajustado.")
    element_type: str = Field(..., pattern="^(node|edge)$", description="Tipo do elemento ('node' ou 'edge').")
    # Usar nomes distintos para evitar ambiguidade
    new_weight: Optional[float] = Field(None, ge=0.0, le=1.0, description="Novo peso para a hiperaresta (0.0 a 1.0).")
    new_relevance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Nova relevância para o nó (0.0 a 1.0).")

    @validator('*', pre=True, always=True)
    def check_value_based_on_type(cls, v, values, field):
        """Valida que apenas o valor relevante (peso ou relevância) é fornecido."""
        element_type = values.get('element_type')
        if field.name == 'new_weight' and element_type == 'node' and v is not None:
            raise ValueError("Não se pode definir 'new_weight' para um 'node'. Use 'new_relevance'.")
        if field.name == 'new_relevance' and element_type == 'edge' and v is not None:
            raise ValueError("Não se pode definir 'new_relevance' para uma 'edge'. Use 'new_weight'.")
        if field.name == 'new_weight' and element_type == 'edge' and v is None:
             # Permitir None inicialmente, mas o endpoint pode exigir
             pass
        if field.name == 'new_relevance' and element_type == 'node' and v is None:
             # Permitir None inicialmente, mas o endpoint pode exigir
             pass
        return v

class HoTDataResponse(BaseModel):
    """Modelo para a resposta com os dados do HoT."""
    nodes: List[Dict[str, Any]] = Field(..., description="Lista de nós no hipergrafo.")
    edges: List[Dict[str, Any]] = Field(..., description="Lista de hiperarestas no hipergrafo.")
    metadata: Dict[str, Any] = Field(..., description="Metadados sobre o estado do HoT.")

class HoTMetricsResponse(BaseModel):
    """Modelo para a resposta com as métricas do HoT."""
    node_count: int
    edge_count: int
    avg_hyperedge_size: float
    avg_node_degree: float
    graph_density: float
    avg_graph_centrality: float
    # Adicionar outras métricas conforme necessário

class HoTInsightsResponse(BaseModel):
    """Modelo para a resposta com os insights do HoT."""
    insights: List[str] = Field(..., description="Lista de insights gerados a partir do HoT.")

class HoTAdjustmentResponse(BaseModel):
    """Modelo para a resposta de ajuste do HoT."""
    status: str
    message: str
    element_id: str
    element_type: str
    new_value: float

# --- API Router ---

router = APIRouter()

# Injetar dependência do HoTService
def get_hot_service_dependency() -> HoTService:
    return get_hot_service()

# --- Endpoints ---

@router.get("/current", response_model=HoTDataResponse, tags=["Hypergraph of Thoughts"])
async def get_current_hot(
    hot_service: HoTService = Depends(get_hot_service_dependency)
) -> HoTDataResponse:
    """
    Retorna a representação atual do Hipergrafo de Pensamentos (HoT)
    para visualização no frontend.
    """
    logger.info("Requisição para obter estado atual do HoT.")
    try:
        hot_data = hot_service.get_current_hot_data()
        # Validar se a estrutura está correta antes de retornar
        if "nodes" not in hot_data or "edges" not in hot_data or "metadata" not in hot_data:
             logger.error("Estrutura de dados do HoT inválida retornada pelo serviço.")
             raise HTTPException(status_code=500, detail="Erro interno ao formatar dados do HoT.")
        return HoTDataResponse(**hot_data)
    except Exception as e:
        logger.error(f"Erro ao obter estado atual do HoT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao buscar dados do HoT.")

@router.get("/metrics", response_model=HoTMetricsResponse, tags=["Hypergraph of Thoughts"])
async def get_hot_metrics(
    hot_service: HoTService = Depends(get_hot_service_dependency)
) -> HoTMetricsResponse:
    """
    Calcula e retorna métricas sobre o estado atual do HoT.
    """
    logger.info("Requisição para obter métricas do HoT.")
    try:
        metrics = hot_service.calculate_hot_metrics()
        return HoTMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Erro ao calcular métricas do HoT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao calcular métricas do HoT.")

@router.get("/insights", response_model=HoTInsightsResponse, tags=["Hypergraph of Thoughts"])
async def get_hot_insights(
    hot_service: HoTService = Depends(get_hot_service_dependency)
) -> HoTInsightsResponse:
    """
    Gera e retorna insights baseados no estado atual do HoT.
    """
    logger.info("Requisição para obter insights do HoT.")
    try:
        insights = hot_service.generate_hot_insights()
        return HoTInsightsResponse(insights=insights)
    except Exception as e:
        logger.error(f"Erro ao gerar insights do HoT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao gerar insights do HoT.")

@router.post("/adjust", response_model=HoTAdjustmentResponse, tags=["Hypergraph of Thoughts"])
async def adjust_hot(
    adjustment: HoTAdjustmentRequest,
    hot_service: HoTService = Depends(get_hot_service_dependency)
) -> HoTAdjustmentResponse:
    """
    Aplica um ajuste (peso de aresta ou relevância de nó) a um elemento do HoT,
    conforme solicitado pelo usuário no frontend.
    """
    logger.info(f"Recebida requisição de ajuste para HoT: ID={adjustment.element_id}, Tipo={adjustment.element_type}")

    # Determinar o valor a ser ajustado
    new_value: Optional[float] = None
    if adjustment.element_type == 'node':
        if adjustment.new_relevance is None:
             raise HTTPException(status_code=422, detail="O campo 'new_relevance' é obrigatório para ajustar um 'node'.")
        new_value = adjustment.new_relevance
    elif adjustment.element_type == 'edge':
        if adjustment.new_weight is None:
             raise HTTPException(status_code=422, detail="O campo 'new_weight' é obrigatório para ajustar uma 'edge'.")
        new_value = adjustment.new_weight

    if new_value is None: # Segurança adicional
         raise HTTPException(status_code=422, detail="Nenhum valor de ajuste (peso ou relevância) fornecido.")

    try:
        success = hot_service.adjust_hot_element(
            element_id=adjustment.element_id,
            element_type=adjustment.element_type,
            new_value=new_value
        )

        if success:
            logger.info(f"Ajuste aplicado com sucesso: ID={adjustment.element_id}, Novo Valor={new_value}")
            return HoTAdjustmentResponse(
                status="success",
                message="Ajuste aplicado com sucesso.",
                element_id=adjustment.element_id,
                element_type=adjustment.element_type,
                new_value=new_value
            )
        else:
            logger.warning(f"Falha ao aplicar ajuste: Elemento não encontrado ou valor inválido. ID={adjustment.element_id}")
            # Usar 404 se o elemento não foi encontrado, 400 se o valor era inválido (embora Pydantic deva pegar isso)
            raise HTTPException(status_code=404, detail=f"Elemento '{adjustment.element_id}' do tipo '{adjustment.element_type}' não encontrado ou valor inválido.")

    except ValueError as e: # Captura erros de validação do HoTService
        logger.warning(f"Erro de valor ao ajustar HoT: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro inesperado ao ajustar HoT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao aplicar ajuste no HoT.")
