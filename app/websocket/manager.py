from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id:int):
        await websocket.accept()
        self.active_connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, websocket: WebSocket, user_id:int):
        self.active_connections.get(user_id, set()).discard(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, sender: WebSocket | None = None):
        for key, values in list(self.active_connections.items()):
            for value in list(values):
                if value is sender:
                    continue
                else:
                    await value.send_text(message)


manager = ConnectionManager()


# Since we changed our manage.py, now we have to do the implementations inside our main.py wherever we used manager!