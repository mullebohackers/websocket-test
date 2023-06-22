#!/usr/bin/env python

import asyncio
import json
import secrets
import logging

import websockets


async def handler(websocket):
    async for message in websocket:
        # event = json.loads(message)
        logging.info(f"websocket message recieved: {message}")
        pass
        # Do nothing! Just a stub.
        await websocket.send(f"Echo: {message}")


async def websocket_server(port:int):
    """
    Start a websocket server. All new connections are sent to "handler".
    
    """
    logging.info(f"Starting websocket-server. Listens on port {port}")
    await websockets.serve(handler, port=port)        # Set up a websocket handler