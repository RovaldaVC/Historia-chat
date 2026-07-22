# Historia Chat

Historia-chat is a text messaging application backend built with FastAPI. It handles real-time delivery over WebSockets, persists messages in a SQL database, and includes a dedicated security module for authentication, with interactive API docs via Swagger UI and ReDoc. Currently in active beta development.

> ❕- Portfolio Project.

## Setup

**Clone the repository**
git clone <repo-url>
cd <project-folder>

**Install dependencies**
pip install -e .

**Run the server**
cd app
uvicorn app.main:app --reload

The API will be available at http://127.0.0.1:8000.


## Project Structure
.
├── app

│   ├── database # SQLAlchemy models, schemas, and session management

│   │   ├── crud.py # Endpoint's core logic

│   │   ├── database.py # Database Setup

│   │   ├── __init__.py

│   │   ├── models.py # Tables of database

│   │   └── schemas.py # schemas and response models

│   ├── __init__.py

│   ├── main.py # Endpoints

│   ├── security # Authentication, hashing, and token generation

│   │   ├── authentication.py # Authorization Setup

│   │   ├── hash_password.py

│   │   ├── hash_session.py

│   │   └── __init__.py

│   └── websocket # WebSocket connection managers and event handlers

│       └── manager.py

├── excalidraw # Architecture diagrams and system design

│   ├── 1_setup.excalidraw

│   ├── 2_security_setup.excalidraw

│   ├── 3_feedback.excalidraw

│   ├── 4_fixed_bugs.excalidraw

│   ├── 5_websocket_setup.excalidraw

│   ├── 6_user_interface.excalidraw

│   ├── 7_chat_logic.excalidraw

│   ├── 8_fix_bugs.excalidraw

│   └── 9.excalidraw

├── pyproject.toml

├── README.md

├── SECURITY.md

└── tests # Unit and integration tests - ⚠️ Beta Mode

    ├── test_app_imports.py
    
    ├── test_chat_creation.py
    
    └── test_websocket_message_storage.py

## API Documentation
Once the server is running, interactive docs are available at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## License
MIT
