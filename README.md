# Kolga Microservice Demo

This project consist of three (3) services. They all talk to each other
either over an API or AMQP.

## Scores API
An API written in FastAPI that provides the following endpoints:

GET /scores - Get scores from the database
POST /scores - {score: <score>, user: <username>} - Create new scores into the database

### Dataflow
When new data comes in from a POST call to the REST api, that data is pushed on a queue
to RabbitMQ over AMQP.

## Reporter Frontend
A webpage rendered with FastAPI and a WebSocket server that the rendered webpage uses for
live updates of scores.

### Dataflow
Initial data pull happens by pulling scores from the Scores API. This happens over a
GET HTTP call.

New content is pulled in over AMQP from RabbitMQ. When new data comes in on the queue
that content is pushed to the HTTP page over a websocket.

## Slack Poster
A background service without a frontend that posts new scores to Slack.

### Dataflow
New content is pulled in over AMQP from RabbitMQ. When new data comes in on the queue
that content is pushed Slack through their REST API.
