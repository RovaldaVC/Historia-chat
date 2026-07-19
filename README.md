# Text Message App (Beta)

A simple text messaging application built with **FastAPI** and a **SQL database**.

> ⚠️ Beta version — under active development.

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

## Licsence
MIT
