import structlog
import json
import sys
from pathlib import Path

# Путь к файлу с логами (в папке build)
LOG_FILE = Path("build") / "server.log"

def file_json_log_processor():
    """
    Возвращает функцию, которая будет записывать event_dict в LOG_FILE как JSON.
    """
    def processor(logger, method_name, event_dict):
        # Откроем файл в режиме 'append' и добавим JSON-строку
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            # Превратим event_dict в JSON-строку
            line = json.dumps(event_dict, ensure_ascii=False)
            f.write(line + "\n")
        return event_dict  # передаём дальше следующему процессору
    return processor

def configure_logging():
    """
    Настраивает structlog без участия стандартного logging:
      1) Пишет JSON-строки в build/server.log
      2) Выводит "человеко-читаемые" логи в консоль
    """
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso", utc=False),
            file_json_log_processor(),                 # Запись в файл JSON
            structlog.dev.ConsoleRenderer()            # Вывод в консоль
        ],
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True
    )
    return structlog.get_logger()
