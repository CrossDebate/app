import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, validator, ValidationError, AnyHttpUrl
from dotenv import load_dotenv
import logging

# Carregar variáveis de ambiente de um arquivo .env (opcional)
# Procura por um arquivo .env na raiz do projeto ou no diretório atual
project_root = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=project_root / ".env")

# Configuração básica de logging para o próprio módulo de config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.config")

# --- Constantes e Padrões ---
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
DEFAULT_MODELS_DIR = "C:/crossdebate/models" # Diretório padrão dos modelos GGUF
DEFAULT_N_CTX = 2048
DEFAULT_N_THREADS = 4
DEFAULT_GPU_LAYERS = 0
DEFAULT_MAX_CONCURRENT_MODELS = 3
DEFAULT_MEMORY_THRESHOLD = 85.0

# --- Modelos Pydantic para Validação ---

class ServerConfig(BaseModel):
    host: str = Field(default=os.getenv("API_HOST", DEFAULT_HOST))
    port: int = Field(default=int(os.getenv("API_PORT", DEFAULT_PORT)), ge=1, le=65535)
    log_level: str = Field(default=os.getenv("API_LOG_LEVEL", DEFAULT_LOG_LEVEL).upper())

    @validator('log_level')
    def validate_log_level(cls, v):
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Log level inválido")
        return v

class DatabaseConfig(BaseModel):
    # Exemplo se usar banco de dados (ajustar conforme necessário)
    url: Optional[str] = Field(default=os.getenv("DATABASE_URL", None))
    pool_size: int = Field(default=int(os.getenv("DB_POOL_SIZE", 5)), ge=1)
    max_overflow: int = Field(default=int(os.getenv("DB_MAX_OVERFLOW", 10)), ge=0)

class GGUFModelConfig(BaseModel):
    models_dir: str = Field(default=os.getenv("CROSSDEBATE_MODELS_DIR", DEFAULT_MODELS_DIR))
    default_n_ctx: int = Field(default=int(os.getenv("CROSSDEBATE_N_CTX", DEFAULT_N_CTX)), ge=512)
    default_n_threads: int = Field(default=int(os.getenv("CROSSDEBATE_N_THREADS", DEFAULT_N_THREADS)), ge=1)
    default_n_gpu_layers: int = Field(default=int(os.getenv("CROSSDEBATE_GPU_LAYERS", DEFAULT_GPU_LAYERS)), ge=0)
    max_concurrent_models: int = Field(default=int(os.getenv("CROSSDEBATE_MAX_MODELS", DEFAULT_MAX_CONCURRENT_MODELS)), ge=1)
    memory_threshold_percent: float = Field(default=float(os.getenv("CROSSDEBATE_MEM_THRESHOLD", DEFAULT_MEMORY_THRESHOLD)), ge=0.0, le=100.0)
    # Opcional: Mapeamento de nomes para caminhos específicos se necessário
    # specific_models: Dict[str, str] = Field(default_factory=dict)

class HoTConfig(BaseModel):
    max_context_nodes: int = Field(default=int(os.getenv("HOT_MAX_CONTEXT_NODES", 5)), ge=1)
    max_context_tokens: int = Field(default=int(os.getenv("HOT_MAX_CONTEXT_TOKENS", 512)), ge=64)
    default_edge_weight: float = Field(default=float(os.getenv("HOT_DEFAULT_EDGE_WEIGHT", 0.5)), ge=0.0, le=1.0)
    default_node_relevance: float = Field(default=float(os.getenv("HOT_DEFAULT_NODE_RELEVANCE", 0.5)), ge=0.0, le=1.0)

class APIConfig(BaseModel):
    # Exemplo: Chaves de API para serviços externos (CARREGAR DO AMBIENTE!)
    openai_api_key: Optional[str] = Field(default=os.getenv("OPENAI_API_KEY", None))
    # Adicionar outras configurações de API, como URLs base, timeouts, etc.
    allowed_origins: List[str] = Field(default=["http://localhost", "http://localhost:8080", "http://127.0.0.1:8080"])

class AppConfig(BaseModel):
    """Configuração principal da aplicação."""
    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    gguf_models: GGUFModelConfig = Field(default_factory=GGUFModelConfig)
    hot: HoTConfig = Field(default_factory=HoTConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    log_dir: str = Field(default=os.getenv("LOG_DIR", str(project_root / "logs")))

    class Config:
        validate_assignment = True # Validar ao atribuir valores

# --- Carregamento e Validação ---

_config_instance: Optional[AppConfig] = None
_config_lock = Lock()

def load_and_validate_config() -> AppConfig:
    """
    Carrega a configuração de variáveis de ambiente e valida usando Pydantic.
    Retorna a instância validada de AppConfig.
    """
    global _config_instance
    if _config_instance is None: # Evita recarregar desnecessariamente
        with _config_lock:
            if _config_instance is None: # Double-check locking
                logger.info("Carregando e validando configuração da aplicação...")
                try:
                    # Pydantic tentará preencher a partir dos defaults, que usam os.getenv
                    config_data = {} # Pode ser estendido para carregar de um arquivo YAML/JSON também
                    _config_instance = AppConfig(**config_data)

                    # Validar caminhos de diretório
                    gguf_dir = Path(_config_instance.gguf_models.models_dir)
                    if not gguf_dir.is_dir():
                         logger.warning(f"Diretório de modelos GGUF não encontrado: {gguf_dir}. Tentando criar...")
                         try:
                             gguf_dir.mkdir(parents=True, exist_ok=True)
                         except Exception as e_dir:
                             logger.error(f"Não foi possível criar o diretório de modelos: {e_dir}")
                             # Considerar levantar um erro mais sério aqui se o diretório for essencial

                    log_dir = Path(_config_instance.log_dir)
                    if not log_dir.is_dir():
                         logger.warning(f"Diretório de logs não encontrado: {log_dir}. Tentando criar...")
                         try:
                             log_dir.mkdir(parents=True, exist_ok=True)
                         except Exception as e_dir:
                             logger.error(f"Não foi possível criar o diretório de logs: {e_dir}")


                    logger.info("Configuração carregada e validada com sucesso.")

                except ValidationError as e:
                    logger.error(f"Erro de validação na configuração: {e}")
                    # Lançar um erro crítico ou sair, pois a config está inválida
                    raise SystemExit(f"Configuração inválida: {e}")
                except Exception as e:
                    logger.error(f"Erro inesperado ao carregar configuração: {e}", exc_info=True)
                    raise SystemExit(f"Erro fatal ao carregar configuração: {e}")

    return _config_instance

# --- Função de Acesso Global ---

def get_config() -> AppConfig:
    """
    Retorna a instância global e validada da configuração da aplicação.
    Carrega e valida na primeira chamada.
    """
    return load_and_validate_config()

# --- Exemplo de Uso (Opcional) ---
if __name__ == "__main__":
    try:
        config = get_config()
        print("Configuração Carregada:")
        print(f"  Host Servidor: {config.server.host}")
        print(f"  Porta Servidor: {config.server.port}")
        print(f"  Diretório Modelos GGUF: {config.gguf_models.models_dir}")
        print(f"  Máx Modelos Concorrentes: {config.gguf_models.max_concurrent_models}")
        print(f"  Contexto HoT (Nós): {config.hot.max_context_nodes}")
        print(f"  Contexto HoT (Tokens): {config.hot.max_context_tokens}")
        print(f"  Log Dir: {config.log_dir}")
        # print(f"  Database URL: {config.database.url}") # Cuidado ao printar URLs com senhas
        print(f"  OpenAI Key Presente: {'Sim' if config.api.openai_api_key else 'Não'}")

        # Testar validação de atribuição
        # config.server.port = 99999 # Isso levantaria um ValidationError
        # config.gguf_models.memory_threshold_percent = 110.0 # Isso levantaria um ValidationError

    except Exception as e:
        print(f"\nErro ao acessar configuração: {e}")
