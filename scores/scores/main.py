import asyncio
import json
import os
from typing import List

import uvicorn
from aio_pika import Message, connect, ExchangeType, DeliveryMode
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, get_db

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

models.Base.metadata.create_all(bind=engine)

BROKER_URL = os.getenv("BROKER_URL", "amqp://therabbit:therabbit@127.0.0.1:5672")

app = FastAPI()


async def send_message(loop, score: schemas.Score):
    message = json.dumps(score.dict()).encode()

    connection = await connect(BROKER_URL, loop=loop)

    # Creating a channel
    channel = await connection.channel()

    scores_exchange = await channel.declare_exchange("scores", ExchangeType.FANOUT)

    # Sending the message
    await scores_exchange.publish(
        Message(message, delivery_mode=DeliveryMode.PERSISTENT), routing_key="kolga"
    )

    print(f" [x] Sent '{message}'")

    await connection.close()


@app.get("/healthz")
def read_healthz():
    return {"Status": 200}


@app.get("/readiness")
def read_readiness():
    return {"Status": 200}


@app.post("/scores")
async def create_scores(
    score: schemas.Score, db: Session = Depends(get_db)
) -> schemas.Score:
    score_record = models.Score(**score.dict())
    db.add(score_record)
    db.commit()

    loop = asyncio.get_event_loop()
    loop.create_task(send_message(loop, score))

    return score_record


@app.get("/scores")
def get_scores(db: Session = Depends(get_db)) -> List[models.Score]:
    return [entry for entry in db.query(models.Score).all()]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
