# tests/test_logging_setup.py
from pathlib import Path
import logging
from utils.logging import setup_logging

def test_setup_logging(tmp_path: Path):
    log_dir = tmp_path / "logs"
    log_path = setup_logging(level="INFO", log_dir=log_dir, console=False)
    logging.getLogger(__name__).info("Linea de prueba")
    assert log_path.exists(), "El archivo de log no se creó"
    content = log_path.read_text(encoding="utf-8")
    assert "Linea de prueba" in content
