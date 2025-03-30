import logging
import time
import os
import sys
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime

# --- Adicionar diretório raiz ao PYTHONPATH ---
# Isso garante que possamos importar módulos de 'backend', 'utils', etc.
# Ajuste o número de '..' conforme necessário dependendo de onde você executa o script.
# Se executar da raiz do projeto, isso pode não ser estritamente necessário,
# mas é uma boa prática para garantir que funcione em diferentes contextos.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # Assume que main.py está em backend/
sys.path.insert(0, project_root)
# --- Fim da adição ao PYTHONPATH ---

# --- Importações do Projeto (Serão criadas/refinadas depois) ---
# from backend.api import chat, hot, analysis_endpoints, settings, models_api, performance_api, visualization_api # Exemplo de como importar routers
# from backend.services.gguf_service import GGUFService # Exemplo
# from backend.services.hot_service import HoTService # Exemplo
from backend.utils.logging_config import setup_advanced_logger # Usaremos nosso logger avançado

# --- Configuração do Logging ---
# Usar o logger avançado configurado em utils
# O ideal é ter um arquivo de configuração central (config.py) que define LOG_DIR
LOG_DIR = os.path.join(project_root, "logs")
logger = setup_advanced_logger(LOG_DIR, "backend_api", log_level=logging.INFO)

# --- Configuração da Aplicação FastAPI ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código a ser executado na inicialização
    logger.info("Iniciando a aplicação CrossDebate Backend...")
    # Inicializar serviços, conexões de banco de dados, etc.
    # Exemplo:
    # app.state.gguf_service = GGUFService()
    # app.state.hot_service = HoTService()
    # await app.state.db_pool = create_db_pool()
    print("Startup complete.")
    yield
    # Código a ser executado no encerramento
    logger.info("Encerrando a aplicação CrossDebate Backend...")
    # Fechar conexões, limpar recursos, etc.
    # Exemplo:
    # await app.state.db_pool.close()
    print("Shutdown complete.")

app = FastAPI(
    title="CrossDebate API",
    description="API Backend para a plataforma CrossDebate, gerenciando interações com modelos GGUF e Hipergrafos de Pensamentos.",
    version="1.0.0",
    lifespan=lifespan # Gerencia inicialização e encerramento
)

# --- Configuração do CORS ---
# Permitir origens específicas em produção
origins = [
    "http://localhost",         # Desenvolvimento
    "http://localhost:8080",    # Servidor HTTP simples padrão
    "http://127.0.0.1",
    "http://127.0.0.1:8080",
    # Adicionar a URL do frontend de produção aqui
    # "https://your-crossdebate-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Ou ["*"] para desenvolvimento irrestrito
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, etc.)
    allow_headers=["*"], # Permite todos os cabeçalhos
)

# --- Middleware para Logging e Performance ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para registrar informações sobre cada requisição e seu tempo de processamento.
    """
    request_id = request.headers.get("X-Request-ID", f"req_{int(time.time()*1000)}")
    logger.info(f"Requisição recebida: ID={request_id} Method={request.method} Path={request.url.path} Client={request.client.host}")
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000 # ms
        response.headers["X-Process-Time-Ms"] = str(process_time)
        logger.info(f"Requisição concluída: ID={request_id} Status={response.status_code} Duration={process_time:.2f}ms")
        return response
    except HTTPException as http_exc:
        # Log HTTPExceptions especificamente
        process_time = (time.time() - start_time) * 1000 # ms
        logger.warning(f"Erro HTTP na requisição: ID={request_id} Status={http_exc.status_code} Detail={http_exc.detail} Duration={process_time:.2f}ms")
        # Re-levantar a exceção para que FastAPI a trate
        raise http_exc
    except Exception as e:
        # Log de erros inesperados
        process_time = (time.time() - start_time) * 1000 # ms
        logger.error(f"Erro interno na requisição: ID={request_id} Error={str(e)} Duration={process_time:.2f}ms", exc_info=True)
        # Retornar uma resposta de erro genérica
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "request_id": request_id}
        )


# --- Endpoints Básicos ---

@app.get("/health", tags=["Status"])
async def health_check() -> Dict[str, str]:
    """
    Verifica a saúde da API. Retorna 'ok' se a API estiver operacional.
    """
    logger.info("Health check solicitado.")
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# --- Inclusão dos Roteadores da API ---
# Descomente e ajuste os imports e includes quando os routers forem criados

# from backend.api import chat, hot, analysis_endpoints, settings, models_api, performance_api, visualization_api
# app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
# app.include_router(hot.router, prefix="/api/hot", tags=["Hypergraph of Thoughts"])
# app.include_router(analysis_endpoints.router, prefix="/api/analysis", tags=["Analysis"])
# app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
# app.include_router(models_api.router, prefix="/api", tags=["Models"]) # Endpoint /api/models já existe aqui
# app.include_router(performance_api.router, prefix="/api/performance", tags=["Performance"])
# app.include_router(visualization_api.router, prefix="/api/visualization", tags=["Visualization"])

# --- Execução do Servidor (se este arquivo for executado diretamente) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor Uvicorn para desenvolvimento...")
    # Use --reload para desenvolvimento, mas não em produção
    # O host 0.0.0.0 torna a API acessível na rede local
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
