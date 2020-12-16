import asyncio
import json
import os
from typing import List

import aiohttp

import uvicorn
from aio_pika import IncomingMessage, connect, ExchangeType
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

load_dotenv()

BROKER_URL = os.getenv("BROKER_URL", "amqp://therabbit:therabbit@127.0.0.1:5672/default")
SCORES_API = os.getenv("SCORES_API", "http://scores:8000")
REPORTER_URL = os.getenv("REPORTER_URL", "http://localhost:8001")

REPORTER_PROTOCOL = "https" if "https://" in REPORTER_URL else "http"
WS_PROTOCOL = "wss" if REPORTER_PROTOCOL == "https" else "ws"
WS_URL = REPORTER_URL.replace(REPORTER_PROTOCOL, WS_PROTOCOL)

app = FastAPI()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


html = (
    """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Reporter</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <table>
        <thead>
          <tr>
            <th>Player</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody id='scores'>
        </tbody
        </table>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`"""
    + WS_URL
    + """/ws/${client_id}`);
            ws.onmessage = function(event) {
                console.log("Got message: ", event.data)
                var obj = JSON.parse(event.data);
                if (typeof obj != 'object') return;            
            
                var scores = document.getElementById('scores')
                
                var newScore = document.createElement('tr')
                
                var user = document.createElement('td')
                var score = document.createElement('td')
                var userContent = document.createTextNode(obj.user)
                var scoreContent = document.createTextNode(obj.score)
                user.appendChild(userContent)
                score.appendChild(scoreContent)
                newScore.appendChild(user)
                newScore.appendChild(score)
                scores.appendChild(newScore)
            };
        </script>
    </body>
</html>
"""
)


@app.get("/healthz")
def read_healthz():
    return {"Status": 200}


@app.get("/readiness")
def read_readiness():
    return {"Status": 200}


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)

    async with aiohttp.request("GET", f"{SCORES_API}/scores") as object_names_response:
        if object_names_response.status != 200:
            raise HTTPException(
                status_code=500, detail="Could not get team name suggestions"
            )
        scores: List[str] = await object_names_response.json()
        for score in scores:
            await manager.send_personal_message(json.dumps(score), websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")


async def on_message(message: IncomingMessage):
    """
    on_message doesn't necessarily have to be defined as async.
    Here it is to show that it's possible.
    """
    print(" [x] Received message %r" % message)

    decoded_message = message.body.decode()

    try:
        print(f"Message body is: {json.loads(decoded_message)}")
    except Exception:
        print("Not a JSON message, ignoring")

    print("Broadcasting?")

    await manager.broadcast(decoded_message)

    await asyncio.sleep(5)  # Represents async I/O operations


async def main_amqp(loop):
    # Perform connection
    connection = await connect(BROKER_URL, loop=loop)

    # Creating a channel
    channel = await connection.channel()
    # await channel.set_qos(prefetch_count=1)

    logs_exchange = await channel.declare_exchange("scores", ExchangeType.FANOUT)

    # Declaring queue
    queue = await channel.declare_queue(exclusive=True)

    # Binding the queue to the exchange
    await queue.bind(logs_exchange)

    # Start listening the queue with name 'task_queue'
    await queue.consume(on_message)


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(main_amqp(loop))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="trace")
