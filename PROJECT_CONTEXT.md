# Project Environment

OS: Windows 11

Python:
- Python 3.13.7
- Virtual Environment: .venv

Activation:
.\.venv\Scripts\Activate.ps1

Installed Packages:
- fastapi
- uvicorn
- httpx
- ollama

Ollama:
- URL: http://localhost:11434
- Model: qwen3:8b

Current Project Structure:
ai-backend/
├── main.py
├── database.py
├── conversation.py
├── ollama_client.py
├── task_manager.py
└── voice/

Important:
- Use Windows paths.
- Use Python 3.13 only.
- Never suggest Linux-style .venv/bin paths.
- Never recreate the venv unless explicitly requested.
- Assume dependencies are installed in .venv.