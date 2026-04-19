from __future__ import annotations

import os
from pathlib import Path

from .asr import find_node, find_whisper
from .ocr import find_tesseract


def _env_or_setting(settings: dict, key: str, env_key: str) -> str | None:
    value = os.environ.get(env_key)
    if value:
        return value
    value = settings.get(key)
    if value:
        return str(value)
    return value or None


def _xenova_available(model_root: str | None, model: str | None, node_modules: str | None, node_path: str | None) -> tuple[bool, str | None]:
    if not find_node(node_path):
        return False, "node executable not found"
    if not model_root:
        return False, "xenova_model_root is not configured"
    if not model:
        return False, "xenova_model is not configured"
    model_path = Path(model_root).expanduser() / Path(*model.split("/"))
    if not model_path.exists():
        return False, f"model not found: {model_path}"
    if not node_modules:
        return False, "xenova_node_modules is not configured"
    modules_path = Path(node_modules).expanduser()
    if not (modules_path / "@xenova" / "transformers").exists():
        return False, f"@xenova/transformers not found under {modules_path}"
    if not (modules_path / "wavefile").exists():
        return False, f"wavefile not found under {modules_path}"
    return True, None


def engine_config(settings: dict) -> dict:
    return {
        "ocr_backend": os.environ.get("MEDIA_WORKBENCH_OCR_BACKEND") or settings.get("ocr_backend", "auto"),
        "tesseract_path": _env_or_setting(settings, "tesseract_path", "MEDIA_WORKBENCH_TESSERACT"),
        "asr_backend": os.environ.get("MEDIA_WORKBENCH_ASR_BACKEND") or settings.get("asr_backend", "auto"),
        "whisper_path": _env_or_setting(settings, "whisper_path", "MEDIA_WORKBENCH_WHISPER"),
        "node_path": _env_or_setting(settings, "node_path", "MEDIA_WORKBENCH_NODE"),
        "xenova_model_root": _env_or_setting(settings, "xenova_model_root", "MEDIA_WORKBENCH_XENOVA_MODEL_ROOT"),
        "xenova_model": os.environ.get("MEDIA_WORKBENCH_XENOVA_MODEL") or settings.get("xenova_model", "Xenova/whisper-small"),
        "xenova_node_modules": _env_or_setting(settings, "xenova_node_modules", "MEDIA_WORKBENCH_XENOVA_NODE_MODULES"),
    }


def xenova_engine_status(config: dict) -> tuple[bool, str | None]:
    return _xenova_available(
        config["xenova_model_root"],
        config["xenova_model"],
        config["xenova_node_modules"],
        config["node_path"],
    )


def describe_capabilities(settings: dict) -> dict:
    config = engine_config(settings)
    tesseract_path = find_tesseract(config["tesseract_path"])
    whisper_path = find_whisper(config["whisper_path"])
    node_path = find_node(config["node_path"])
    xenova_ok, xenova_reason = xenova_engine_status(config)

    return {
        "local_first": True,
        "external_enrichment_enabled": bool(settings.get("allow_external_enrichment", False)),
        "config": config,
        "engines": {
            "ocr": [
                {
                    "id": "tesseract",
                    "available": bool(tesseract_path),
                    "path": tesseract_path,
                    "description": "Local Tesseract CLI OCR",
                },
                {
                    "id": "spike",
                    "available": True,
                    "description": "Deterministic local OCR fallback for API testing",
                },
            ],
            "asr": [
                {
                    "id": "xenova",
                    "available": xenova_ok,
                    "unavailable_reason": xenova_reason,
                    "node_path": node_path,
                    "model_root": config["xenova_model_root"],
                    "model": config["xenova_model"],
                    "node_modules": config["xenova_node_modules"],
                    "description": "Local Xenova/Transformers.js Whisper ASR",
                },
                {
                    "id": "whisper-cli",
                    "available": bool(whisper_path),
                    "path": whisper_path,
                    "description": "Local OpenAI Whisper-compatible CLI ASR",
                },
                {
                    "id": "spike",
                    "available": True,
                    "description": "Deterministic local ASR fallback for API testing",
                },
            ],
        },
    }
