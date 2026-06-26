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
uvicorn main:app --reload

The API will be available at http://127.0.0.1:8000.


## Project Structure
├── .gitignore

├── main.py               # FastAPI application entry point

├── project.excalidraw    # Design & progress sketches

├── pyproject.toml        # Project metadata & dependencies

├── README.md

└── schema.py             # Pydantic models / DB schema


## API Documentation
Once the server is running, interactive docs are available at:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Licsence
MIT