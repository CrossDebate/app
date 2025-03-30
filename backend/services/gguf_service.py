import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from llama_cpp import Llama, LlamaGrammar # Import LlamaGrammar if needed for constrained generation
from threading import Lock
from collections import OrderedDict
import psutil

# Importar configuração de logging (assumindo que está em backend/utils)
# Ajuste o import se a estrutura for diferente
try:
    from backend.utils.logging_config import get_logger
    logger = get_logger("gguf_service")
except ImportError:
    # Fallback básico se a estrutura de logging não estiver pronta
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("gguf_service")

# --- Configurações (Podem vir de um arquivo de config central) ---
# O caminho absoluto é mais robusto, mas requer configuração correta.
# Usar um caminho relativo à raiz do projeto pode ser mais portável.
# Assumindo que este script está em backend/services/
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODELS_BASE_DIR = os.environ.get("CROSSDEBATE_MODELS_DIR", "C:/crossdebate/models") # Usar variável de ambiente ou padrão
if not Path(MODELS_BASE_DIR).is_absolute():
     MODELS_BASE_DIR = PROJECT_ROOT / MODELS_BASE_DIR

MAX_CONCURRENT_MODELS = int(os.environ.get("CROSSDEBATE_MAX_MODELS", 3)) # Limite de modelos na memória
MEMORY_THRESHOLD_PERCENT = float(os.environ.get("CROSSDEBATE_MEM_THRESHOLD", 85.0)) # Limite de uso de RAM
DEFAULT_N_CTX = int(os.environ.get("CROSSDEBATE_N_CTX", 2048))
DEFAULT_N_THREADS = int(os.environ.get("CROSSDEBATE_N_THREADS", 4)) # Ajustar conforme CPU
DEFAULT_N_GPU_LAYERS = int(os.environ.get("CROSSDEBATE_GPU_LAYERS", 0)) # 0 para CPU, >0 para GPU offload

class GGUFModelNotFoundError(Exception):
    """Exceção para modelo GGUF não encontrado."""
    pass

class GGUFLoadError(Exception):
    """Exceção para erro ao carregar modelo GGUF."""
    pass

class GGUFGenerationError(Exception):
    """Exceção para erro durante a geração de texto/embedding."""
    pass


class GGUFService:
    """
    Serviço para gerenciar e interagir com modelos GGUF usando llama-cpp-python.
    Implementa cache LRU e gerenciamento básico de memória.
    """
    _instance = None
    _lock = Lock()

    # Usar __new__ para implementar Singleton (garante uma única instância do serviço)
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GGUFService, cls).__new__(cls)
                # Inicialização que só deve ocorrer uma vez
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """Inicializa o serviço GGUF (se ainda não inicializado)."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized: # Double-check locking
                return

            logger.info(f"Inicializando GGUFService (PID: {os.getpid()})...")
            logger.info(f"Diretório base dos modelos: {MODELS_BASE_DIR}")
            logger.info(f"Máximo de modelos concorrentes: {MAX_CONCURRENT_MODELS}")
            logger.info(f"Limite de memória: {MEMORY_THRESHOLD_PERCENT}%")

            self.models_dir = Path(MODELS_BASE_DIR)
            if not self.models_dir.is_dir():
                 logger.warning(f"Diretório de modelos '{self.models_dir}' não encontrado ou não é um diretório.")
                 # Considerar levantar um erro aqui se o diretório for essencial

            # Cache LRU para modelos carregados
            self.model_cache: OrderedDict[str, Llama] = OrderedDict()
            self.model_paths: Dict[str, Path] = {} # Mapeia nome do modelo para path
            self.model_load_status: Dict[str, str] = {} # 'unloaded', 'loading', 'loaded', 'error'

            self._scan_models() # Scan inicial
            self._initialized = True
            logger.info(f"GGUFService inicializado. Modelos encontrados: {len(self.model_paths)}")

    def _scan_models(self):
        """Escaneia o diretório de modelos e atualiza a lista de caminhos."""
        logger.info(f"Escaneando diretório de modelos: {self.models_dir}")
        found_paths = {}
        try:
            if not self.models_dir.is_dir():
                logger.warning(f"Diretório de modelos inválido: {self.models_dir}")
                return

            for file_path in self.models_dir.rglob('*.gguf'): # Busca recursiva
                if file_path.is_file():
                    model_name = file_path.stem # Usa nome do arquivo (sem extensão) como ID
                    found_paths[model_name] = file_path
                    if model_name not in self.model_load_status:
                        self.model_load_status[model_name] = 'unloaded'
            self.model_paths = found_paths
            logger.info(f"Scan completo. {len(self.model_paths)} modelos GGUF encontrados.")
        except Exception as e:
            logger.error(f"Erro durante o scan de modelos: {e}", exc_info=True)

    def list_available_models(self) -> List[Dict[str, Any]]:
        """Retorna a lista de modelos GGUF encontrados e seu status."""
        self._scan_models() # Garante que a lista está atualizada
        model_list = []
        for name, path in self.model_paths.items():
            model_list.append({
                "name": name,
                "path": str(path),
                "status": self.model_load_status.get(name, 'unloaded')
            })
        return model_list

    def get_model_path(self, model_name: str) -> Path:
        """Obtém o caminho completo para um modelo pelo nome."""
        path = self.model_paths.get(model_name)
        if not path or not path.is_file():
            # Tenta re-escanear caso o modelo tenha sido adicionado recentemente
            self._scan_models()
            path = self.model_paths.get(model_name)
            if not path or not path.is_file():
                logger.error(f"Arquivo do modelo GGUF não encontrado para '{model_name}' em {self.models_dir}")
                raise GGUFModelNotFoundError(f"Modelo '{model_name}' não encontrado.")
        return path

    def _check_memory_and_evict(self):
        """Verifica o uso de memória e descarrega modelos se necessário (estratégia LRU)."""
        while len(self.model_cache) >= MAX_CONCURRENT_MODELS or psutil.virtual_memory().percent > MEMORY_THRESHOLD_PERCENT:
            if not self.model_cache:
                logger.warning("Limite de memória excedido, mas nenhum modelo no cache para descarregar.")
                break # Evita loop infinito se não houver nada para remover

            # Remove o modelo menos recentemente usado (primeiro item no OrderedDict)
            oldest_model_name, _ = self.model_cache.popitem(last=False)
            self.model_load_status[oldest_model_name] = 'unloaded'
            logger.info(f"Modelo '{oldest_model_name}' descarregado devido à pressão de memória/limite de cache (LRU).")
            # Forçar coleta de lixo pode ajudar a liberar memória mais rapidamente
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()


    def get_model(self, model_name: str) -> Llama:
        """
        Carrega ou recupera um modelo GGUF do cache (LRU).
        Gerencia o descarregamento de modelos menos usados se o limite for atingido.

        Args:
            model_name (str): O nome do modelo (sem extensão .gguf).

        Returns:
            Llama: A instância carregada do modelo llama_cpp.

        Raises:
            GGUFModelNotFoundError: Se o arquivo do modelo não for encontrado.
            GGUFLoadError: Se ocorrer um erro durante o carregamento.
        """
        with self._lock:
            if model_name in self.model_cache:
                # Move para o final (mais recentemente usado)
                self.model_cache.move_to_end(model_name)
                logger.debug(f"Modelo '{model_name}' recuperado do cache.")
                return self.model_cache[model_name]

            # Verifica memória e descarrega se necessário ANTES de carregar novo modelo
            self._check_memory_and_evict()

            model_path = self.get_model_path(model_name) # Levanta GGUFModelNotFoundError se não encontrado
            logger.info(f"Carregando modelo '{model_name}' de {model_path}...")
            self.model_load_status[model_name] = 'loading'

            try:
                # Parâmetros de carregamento - podem ser configuráveis
                model = Llama(
                    model_path=str(model_path),
                    n_ctx=DEFAULT_N_CTX,
                    n_threads=DEFAULT_N_THREADS,
                    n_gpu_layers=DEFAULT_N_GPU_LAYERS,
                    verbose=False # Reduzir verbosidade do llama-cpp
                    # Outros parâmetros úteis: n_batch, use_mlock, use_mmap
                )
                self.model_cache[model_name] = model
                self.model_load_status[model_name] = 'loaded'
                logger.info(f"Modelo '{model_name}' carregado com sucesso.")
                return model
            except Exception as e:
                self.model_load_status[model_name] = 'error'
                logger.error(f"Falha ao carregar o modelo GGUF '{model_name}': {e}", exc_info=True)
                raise GGUFLoadError(f"Não foi possível carregar o modelo '{model_name}'.") from e

    def generate_response(self, model_name: str, prompt: str, **kwargs) -> str:
        """
        Gera texto usando um modelo GGUF especificado.

        Args:
            model_name (str): Nome do modelo a ser usado.
            prompt (str): O prompt de entrada.
            **kwargs: Argumentos adicionais para Llama.create_completion
                      (e.g., max_tokens, temperature, top_p, stop).

        Returns:
            str: O texto gerado pelo modelo.

        Raises:
            GGUFGenerationError: Se ocorrer um erro durante a geração.
        """
        logger.debug(f"Gerando resposta com modelo '{model_name}'. Prompt: '{prompt[:50]}...'")
        start_time = time.time()
        try:
            model = self.get_model(model_name) # Carrega ou obtém do cache

            # Parâmetros padrão de geração
            generation_params = {
                "max_tokens": 150,
                "temperature": 0.7,
                "top_p": 0.9,
                "stop": ["\n", "Human:", "User:"], # Parar em novas linhas ou identificadores comuns
                "echo": False, # Não repetir o prompt na saída
                **kwargs # Permite sobrescrever padrões
            }

            output = model.create_completion(prompt=prompt, **generation_params)
            response_text = output["choices"][0]["text"].strip()

            duration = time.time() - start_time
            logger.info(f"Resposta gerada por '{model_name}' em {duration:.2f}s. Tokens: {output.get('usage', {}).get('completion_tokens', 'N/A')}")
            return response_text

        except (GGUFModelNotFoundError, GGUFLoadError) as e:
             logger.error(f"Erro ao obter modelo para geração: {e}")
             raise GGUFGenerationError(f"Modelo '{model_name}' indisponível.") from e
        except Exception as e:
            logger.error(f"Erro durante a geração de texto com '{model_name}': {e}", exc_info=True)
            raise GGUFGenerationError(f"Falha na geração com o modelo '{model_name}'.") from e

    def generate_embedding(self, model_name: str, text: str) -> List[float]:
        """
        Gera o embedding para um texto usando um modelo GGUF especificado.

        Args:
            model_name (str): Nome do modelo a ser usado.
            text (str): O texto para gerar o embedding.

        Returns:
            List[float]: O vetor de embedding.

        Raises:
            GGUFGenerationError: Se ocorrer um erro durante a geração do embedding.
        """
        logger.debug(f"Gerando embedding com modelo '{model_name}'. Texto: '{text[:50]}...'")
        start_time = time.time()
        try:
            model = self.get_model(model_name) # Carrega ou obtém do cache
            embedding = model.embed(text)
            duration = time.time() - start_time
            logger.info(f"Embedding gerado por '{model_name}' em {duration:.2f}s. Dimensão: {len(embedding)}")
            return embedding
        except (GGUFModelNotFoundError, GGUFLoadError) as e:
             logger.error(f"Erro ao obter modelo para embedding: {e}")
             raise GGUFGenerationError(f"Modelo '{model_name}' indisponível.") from e
        except Exception as e:
            logger.error(f"Erro durante a geração de embedding com '{model_name}': {e}", exc_info=True)
            raise GGUFGenerationError(f"Falha na geração de embedding com o modelo '{model_name}'.") from e

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Retorna informações sobre um modelo carregado ou disponível."""
        path = self.model_paths.get(model_name)
        if not path:
            return {"error": "Model not found", "name": model_name}

        info = {
            "name": model_name,
            "path": str(path),
            "status": self.model_load_status.get(model_name, 'unloaded'),
            "size_bytes": path.stat().st_size if path.exists() else 0,
            "last_modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat() if path.exists() else None
        }
        if model_name in self.model_cache:
             info["loaded_in_cache"] = True
             # Poderia adicionar mais metadados do objeto Llama se necessário
             # info["n_ctx"] = self.model_cache[model_name].n_ctx() # Exemplo
        else:
             info["loaded_in_cache"] = False
        return info

# --- Singleton Instance ---
# Para garantir que o serviço seja inicializado apenas uma vez
gguf_service_instance = GGUFService()

def get_gguf_service() -> GGUFService:
    """Função para obter a instância singleton do GGUFService."""
    return gguf_service_instance
