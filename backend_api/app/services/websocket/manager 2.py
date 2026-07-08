from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, user_id: int, ws: WebSocket):
        await ws.accept()
        self.active[user_id].append(ws)

    def disconnect(self, user_id: int, ws: WebSocket):
        connections = self.active.get(user_id, [])
        if ws in connections:
            connections.remove(ws)

    async def notify_user(self, user_id: int, message: dict):
        for ws in list(self.active.get(user_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(user_id, ws)


ws_manager = ConnectionManager()
