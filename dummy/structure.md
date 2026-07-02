# Project Structure

```text
ai-backend/
├── main.py
├── config.py
├── requirements.txt
├── structure.md
├── api/
│   ├── __init__.py
│   └── routes.py
├── core/
│   ├── __init__.py
│   ├── conversation.py
│   ├── intent_parser.py
│   ├── memory.py
│   ├── prompt_builder.py
│   └── intent_router.py
├── database/
│   ├── __init__.py
│   ├── db.py
│   ├── models.py
│   └── task_repository.py
├── managers/
│   ├── __init__.py
│   ├── app_manager.py
│   ├── browser_manager.py
│   ├── media_manager.py
│   ├── task_manager.py
│   ├── system_manager.py
│   └── window_manager.py
├── services/
│   ├── __init__.py
│   ├── llm_service.py
│   ├── ollama_service.py
│   └── whisper_service.py
├── utils/
│   ├── __init__.py
│   ├── constants.py
│   ├── entity_matcher.py
│   ├── logger.py
│   └── transcript_corrector.py
├── tests/
│   ├── __init__.py
│   ├── check_schema.py
│   ├── clear_tasks.py
│   ├── debug_volume.py
│   ├── test.py
│   ├── test_browser.py
│   ├── test_intent.py
│   ├── test_lock.py
│   ├── test_router.py
│   ├── test_tts.py
│   ├── test_voice.py
│   ├── test_volume.py
│   └── test_window.py
├── voice/
│   ├── __init__.py
│   ├── README.md
│   ├── stt.py
│   ├── tts.py
│   └── wake_word.py
├── data/
│   ├── nova.db
│   └── screenshots/
├── logs/
```

The refactor preserves the existing behavior while moving implementation modules into clear package boundaries.