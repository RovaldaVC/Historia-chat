# -- Imports -- #
from fastapi import WebSocket

# all the connected websockets are here. based on json format
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, set[WebSocket]] = {}

    # Here we connect the websocket and add it to active list.
    async def connect(self, websocket: WebSocket, user_id:int):
        await websocket.accept()
        self.active_connections.setdefault(user_id, set()).add(websocket)

    # Here we disconnect the websocket and remove it from active list
    def disconnect(self, websocket: WebSocket, user_id:int):
        self.active_connections.get(user_id, set()).discard(websocket)

    # Here we send a message via websocket and handle the string input problem(instead of json).
    async def send_personal_message(self, message: str | dict, websocket: WebSocket):
        if isinstance(message, dict):
            await websocket.send_json(message)
        else:
            await websocket.send_text(message)

    # Here we broadcast the message to everyone excluding the sender.
    async def broadcast(self, message: str | dict, sender: WebSocket | None = None):
        for key, values in list(self.active_connections.items()):
            for value in list(values):
                if value is sender:
                    continue
                if isinstance(message, dict):
                    await value.send_json(message)
                else:
                    await value.send_text(message)

# We import this manager instead of all the functions up here.
manager = ConnectionManager()