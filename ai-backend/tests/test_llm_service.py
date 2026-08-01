import pytest
import json
from unittest.mock import MagicMock, patch
from services.llm.config import LLMConfig
from services.llm.base import LLMProvider
from services.llm.service import LLMService
from services.llm.providers import OllamaProvider

def test_llm_config_loading(tmp_path):
    # Create temp config file
    config_file = tmp_path / "test_config.json"
    config_data = {
        "ollama_url": "http://localhost:9999",
        "default_model": "test-hermes",
        "fallback_model": "test-qwen",
        "temperature": 0.5,
        "streaming": False
    }
    with open(config_file, "w") as f:
        json.dump(config_data, f)

    cfg = LLMConfig(str(config_file))
    assert cfg.ollama_url == "http://localhost:9999"
    assert cfg.default_model == "test-hermes"
    assert cfg.fallback_model == "test-qwen"
    assert cfg.temperature == 0.5
    assert cfg.streaming is False

def test_service_fallback_recovery():
    service = LLMService()
    
    mock_default = MagicMock()
    mock_fallback = MagicMock()
    
    # Configure mock default to fail, and mock fallback to succeed
    mock_default.generate.side_effect = RuntimeError("Connection refused")
    mock_default.model_name = "Hermes"
    mock_fallback.generate.return_value = "Fallback Response"
    mock_fallback.model_name = "Qwen"
    
    service.active_provider = mock_default
    service.fallback_provider = mock_fallback
    service.default_provider = mock_default
    
    response = service.generate("hello")
    
    # Assert default was called, failed, and fallback was called to resolve it
    mock_default.generate.assert_called_once_with("hello", system_prompt=None)
    mock_fallback.generate.assert_called_once_with("hello", system_prompt=None)
    assert response == "Fallback Response"

def test_structured_json_retry_and_fallback():
    service = LLMService()
    
    mock_default = MagicMock()
    mock_fallback = MagicMock()
    
    # First call to default returns malformed json, second call returns malformed json too (triggering fallback)
    mock_default.structured_output.side_effect = json.JSONDecodeError("Invalid control character", "test", 0)
    mock_default.model_name = "Hermes"
    
    expected_data = {"intent": "add_task", "task": "study"}
    mock_fallback.structured_output.return_value = expected_data
    mock_fallback.model_name = "Qwen"
    
    service.active_provider = mock_default
    service.fallback_provider = mock_fallback
    service.default_provider = mock_default
    
    result = service.structured_output("extract intent")
    
    # Default is tried, fails, retried on default, fails, then calls fallback
    assert mock_default.structured_output.call_count == 2
    mock_fallback.structured_output.assert_called_once_with("extract intent", schema=None, system_prompt=None)
    assert result == expected_data

def test_auto_model_selection_rankings():
    service = LLMService()
    
    mock_default = MagicMock()
    mock_fallback = MagicMock()
    
    # Case 1: Hermes is healthy -> active is Hermes
    mock_default.health.return_value = True
    mock_default.model_name = "Hermes"
    mock_fallback.health.return_value = True
    mock_fallback.model_name = "Qwen"
    
    service.default_provider = mock_default
    service.fallback_provider = mock_fallback
    
    service.select_model("AUTO")
    assert service.active_provider == mock_default
    
    # Case 2: Hermes is down, Qwen is healthy -> active is Qwen
    mock_default.health.return_value = False
    service.select_model("AUTO")
    assert service.active_provider == mock_fallback
