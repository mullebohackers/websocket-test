#!/usr/bin/env python

import os
import json
from json.decoder import JSONDecodeError
import logging
from datetime import date, datetime, timedelta

from jose import JWTError, jwt

import websockets

from motor.motor_asyncio import AsyncIOMotorClient


"""
Environment
"""
MONGO_ROOT_PWD = os.getenv('MONGO_ROOT_PWD')                              # MONGO_DB root password (no default)
MONGO_HOST = os.getenv('MONGO_HOST',"mongodb.mongodb")                    # Default mongo host is a Kubernetes service
# MONGO_URI = os.getenv('MONGO_URI',"mongodb://localhost:27017")          # MONGO_DB adress and port

SECRET_KEY = os.getenv('JWT_SECRET_KEY',"347f6e1cd2cf2dadbe5cee95a6d08d70b16097b37b04975b0f25f27fd784f933")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


"""
Globals!  
"""
mongo_db = None


def create_access_token(data: dict, expires_in_hours:int=ACCESS_TOKEN_EXPIRE_HOURS):
    """
    Dummy doc string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=expires_in_hours)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def find_or_create_user(user, group):
    user_id = f"{user}:{group}"
    collection = mongo_db.users
    user_info = await collection.find_one({'_id':user_id})

async def error(websocket, message):
    """
    Send an error message.
    """
    event = {"type": "error", "message": message}
    await websocket.send(json.dumps(event))


async def run_app(websocket):
    """
    Dummy doc string
    """
    async for message in websocket:
        try:
            event = json.loads(message)
        except JSONDecodeError:
            await error(websocket, "Payload is not JSON")
            return
        event = {"type": "echo", "message": event}
        await websocket.send(json.dumps(event))


async def new_connection(websocket):
    """
    Dummy doc string
    """
    message = await websocket.recv()
    try:
        event = json.loads(message)
    except JSONDecodeError:
        await error(websocket, "Payload is not JSON")
        return
    if event.get("type") != "init":
        await error(websocket, "First message must be an init event")
        return
    if 'authInfo' in event:
        user = event['authInfo'].get('user')
        group = event['authInfo'].get('group')
        group_key = event['authInfo'].get('groupKey')
        access_token = create_access_token(data={"sub": f"{user}:{group}"})
    elif 'authToken' in event:
        try:
            payload = jwt.decode(event['authToken'], SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError as ex:        # Error in JWT. Probably expired
            await error(websocket, f"Error {str(ex)} when decoding JWT")
            return
        user, group = tuple(payload.get("sub").split(':'))
        access_token = create_access_token(data={"sub": f"{user}:{group}"})     # Refresh token
    else:
        await error(websocket, "Mising authInfo or authToken in init event")
        return

    event = {"type": "accessToken","token": access_token}
    await websocket.send(json.dumps(event))

    await run_app(websocket)        # Run the app loop until connection is closed


async def websocket_server(port:int):
    """
    Start a websocket server. All new connections are sent to "new_connection".    
    """
    global mongo_db

    logging.info(f"Starting websocket-server. Listens on port {port}")

    # mongo_client = AsyncIOMotorClient(f"mongodb://root:{MONGO_ROOT_PWD}@{MONGO_HOST}:27017")
    # mongo_db = mongo_client.DB1

    await websockets.serve(new_connection, port=port)        # Set up a websocket new_connections