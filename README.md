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
├───app

│   ├───database

│   ├───security

│   └───websocket

├───excalidraw

└───tests

## API Documentation
Once the server is running, interactive docs are available at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## License
MIT
