import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Dict, Any
import sys
import platform
import json
from datetime import datetime

# --- Configurações Padrão ---
DEFAULT_LOG_DIR = "logs"
DEFAULT_LOG_FILE = "backend_app.log"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_FORMAT = "%(asctime)s - %(name)s - [%(levelname)s] - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
MAX_FILE_SIZE_MB = 10
BACKUP_COUNT = 5

# --- Variáveis Globais ---
_loggers: Dict[str, logging.Logger] = {}
_log_dir_path: Optional[Path] = None
_initialized = False

class JsonFormatter(logging.Formatter):
    """Formatador para saída de log em JSON."""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "process_id": record.process,
            "hostname": platform.node(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            log_entry.update(record.extra_data) # Adiciona dados extras

        # Remover chaves padrão que já estão no dicionário
        for key in ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
                    'funcName', 'levelname', 'levelno', 'lineno', 'module',
                    'msecs', 'message', 'msg', 'name', 'pathname', 'process',
                    'processName', 'relativeCreated', 'stack_info', 'thread',
                    'threadName']:
            if hasattr(record, key):
                # Não incluir chaves padrão redundantes no JSON final
                pass

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    log_dir: str = DEFAULT_LOG_DIR,
    log_file: str = DEFAULT_LOG_FILE,
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    max_bytes: int = MAX_FILE_SIZE_MB * 1024 * 1024,
    backup_count: int = BACKUP_COUNT,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_json: bool = False, # JSON desabilitado por padrão nesta versão simples
    json_log_file: Optional[str] = None
) -> None:
    """
    Configura o sistema de logging globalmente.

    Args:
        log_dir (str): Diretório para armazenar os arquivos de log.
        log_file (str): Nome do arquivo de log principal (texto).
        log_level (int): Nível mínimo de log a ser registrado (e.g., logging.INFO).
        log_format (str): Formato da string de log para handlers de texto.
        date_format (str): Formato da data/hora nos logs.
        max_bytes (int): Tamanho máximo do arquivo de log antes da rotação.
        backup_count (int): Número de arquivos de log de backup a serem mantidos.
        enable_console (bool): Habilita o logging para o console (stdout/stderr).
        enable_file (bool): Habilita o logging para um arquivo de texto rotativo.
        enable_json (bool): Habilita o logging para um arquivo JSON rotativo.
        json_log_file (Optional[str]): Nome do arquivo de log JSON (se habilitado).
    """
    global _log_dir_path, _initialized
    if _initialized:
        logging.getLogger(__name__).warning("Sistema de logging já inicializado.")
        return

    _log_dir_path = Path(log_dir)
    try:
        _log_dir_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        logging.error(f"Não foi possível criar o diretório de log '{_log_dir_path}': {e}", exc_info=True)
        # Tenta usar um diretório temporário como fallback
        import tempfile
        _log_dir_path = Path(tempfile.gettempdir()) / "crossdebate_logs"
        _log_dir_path.mkdir(parents=True, exist_ok=True)
        logging.warning(f"Usando diretório de log temporário: {_log_dir_path}")


    # Configurar o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Limpar handlers existentes para evitar duplicação
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    # Criar formatador de texto
    text_formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

    # Handler do Console
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(text_formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

    # Handler de Arquivo de Texto Rotativo
    if enable_file:
        try:
            text_file_path = _log_dir_path / log_file
            file_handler = logging.handlers.RotatingFileHandler(
                filename=text_file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(text_formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.error(f"Não foi possível configurar o handler de arquivo de texto: {e}", exc_info=True)

    # Handler de Arquivo JSON Rotativo
    if enable_json:
        try:
            json_file = json_log_file or log_file.replace(".log", ".jsonl")
            json_file_path = _log_dir_path / json_file
            json_file_handler = logging.handlers.RotatingFileHandler(
                filename=json_file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            json_file_handler.setFormatter(JsonFormatter())
            json_file_handler.setLevel(log_level)
            root_logger.addHandler(json_file_handler)
        except Exception as e:
            logging.error(f"Não foi possível configurar o handler de arquivo JSON: {e}", exc_info=True)

    _initialized = True
    logging.getLogger(__name__).info(f"Sistema de logging inicializado. Nível: {logging.getLevelName(log_level)}. Diretório: {_log_dir_path}")


def get_logger(name: str) -> logging.Logger:
    """
    Retorna uma instância de logger configurada para um módulo específico.

    Se o logging global ainda não foi configurado, ele será inicializado
    com as configurações padrão.

    Args:
        name (str): O nome do logger (geralmente __name__).

    Returns:
        logging.Logger: A instância do logger configurada.
    """
    global _initialized
    if not _initialized:
        print(f"Aviso: Logging não inicializado explicitamente. Usando configurações padrão para logger '{name}'.")
        setup_logging() # Inicializa com padrões se ainda não foi feito

    return logging.getLogger(name)

# --- Inicialização Padrão (Opcional) ---
# Pode ser chamado explicitamente no ponto de entrada da aplicação (ex: main.py)
# setup_logging()

# --- Exemplo de Uso ---
if __name__ == "__main__":
    # Configura o logging (geralmente feito uma vez no início da aplicação)
    setup_logging(log_level=logging.DEBUG, enable_json=True)

    # Obtém loggers para diferentes módulos
    logger_main = get_logger("main_app")
    logger_service = get_logger("my_service")

    # Exemplos de logs
    logger_main.debug("Iniciando aplicação...")
    logger_service.info("Serviço X iniciado com sucesso.")
    logger_main.warning("Configuração Y não encontrada, usando padrão.")
    try:
        result = 10 / 0
    except ZeroDivisionError as e:
        # Log com informações de exceção e dados extras
        logger_service.error(
            "Erro ao realizar cálculo.",
            exc_info=True,
            extra={'extra_data': {'input_value': 10, 'operation': 'division'}}
        )
    logger_main.critical("Falha crítica no sistema!")

    print(f"Logs sendo escritos em: {_log_dir_path}")
