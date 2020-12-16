import asyncio
import json
import os

import uvicorn
from aio_pika import IncomingMessage, connect, ExchangeType
from fastapi import FastAPI
from dotenv import load_dotenv
from slack import WebClient

load_dotenv()

BROKER_URL = os.getenv("BROKER_URL", "amqp://therabbit:therabbit@127.0.0.1:5672")

SLACK_API_TOKEN = os.environ.get("SLACK_API_TOKEN", "")
SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "")
slack_client = WebClient(token=SLACK_API_TOKEN, run_async=True)

app = FastAPI()


@app.get("/healthz")
def read_healthz():
    return {"Status": 200}


@app.get("/readiness")
def read_readiness():
    return {"Status": 200}


async def on_message(message: IncomingMessage):
    """
    on_message doesn't necessarily have to be defined as async.
    Here it is to show that it's possible.
    """
    print(" [x] Received message %r" % message)

    decoded_message = message.body.decode()

    try:
        json_message = json.loads(decoded_message)
    except Exception:
        print("Not a JSON message, ignoring")
        return None

    await slack_client.chat_postMessage(
        channel=SLACK_CHANNEL,
        text=f":tada: {json_message['user']} just scored {json_message['score']} points",
    )


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
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
