#!/usr/bin/env python

import os
import logging
import time
import asyncio
from datetime import date, datetime, timedelta
import json
from json.decoder import JSONDecodeError

from jose import JWTError, jwt

import websockets
from websockets.exceptions import ConnectionClosedOK

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
connections = {}
users = {}

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


async def run_app(websocket, user, group):
    """
    Dummy doc string
    """
    global users

    try:
        for u,v in users[group].items():        # Start by sending position of group users
            event = {'type': "location", 'user': u, 'location': v.get('location'), 'timestamp': v['timestamp']}
            await websocket.send(json.dumps(event))
            # await asyncio.sleep(0.1)  # Don't saturate client

        udata = users[group][user]
        async for message in websocket:         # Event loop
            try:
                event = json.loads(message)
            except JSONDecodeError:
                await error(websocket, "Payload is not JSON")
                return
            
            event_type = event.get('type')
            logging.info(f"Event {event_type} from {user}@{group}")
            if event_type == "location":
                udata['location'] = event.get('location')
                udata['timestamp'] = event.get('timestamp', time.time())
                event = {'type': "location", 'user': user, 'location': udata['location'], 'timestamp': udata['timestamp']}
                websockets.broadcast(connections[group], json.dumps(event))
            else:
                error(websocket, f"Uknown event type: {event_type}")

    except Exception as ex:     # Fatal error!
        logging.error(f"Fatal error: {str(ex)} in connection to user {user}!")
        return          # This will close the failing connection


async def new_connection(websocket):
    """
    Dummy doc string
    """
    global connections

    logging.info("New connection opened")
    try:
        message = await websocket.recv()        # Wait for init event
    except ConnectionClosedOK:      # Conecction was closed before init was sent
        return

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
        userid = f"{user}@{group}"
        access_token = create_access_token(data={"sub": userid})
    elif 'authToken' in event:
        try:
            payload = jwt.decode(event['authToken'], SECRET_KEY, algorithms=[ALGORITHM])
        except JWTError as ex:        # Error in JWT. Probably expired
            await error(websocket, f'Error "{str(ex)}" when decoding JWT')
            return
        userid = payload.get("sub")
        user, group = tuple(userid.split('@'))
        access_token = create_access_token(data={"sub": userid})     # Refresh token
    else:
        await error(websocket, "Mising authInfo or authToken in init event")
        return

    event = {"type": "accessToken", "token": access_token}
    await websocket.send(json.dumps(event))
    logging.info(f"{userid} connected")

    if group not in users:
        users[group] = {}
    # users[group][user] = {'location': {'longitude': 0, 'latitude': 0}, 'timestamp': time.time()}     # Init user record
    users[group][user] = {'timestamp': time.time()}     # Init user record
    if group not in connections:
        connections[group] = set()
    connections[group].add(websocket)   # Save this connection in a list (a set)

    await run_app(websocket, user, group)        # Run the app loop until connection is closed
    connections[group].remove(websocket)    # Remove websocket from connection list
    logging.info(f"{userid} disconnected")


async def websocket_server(port:int):
    """
    Start a websocket server. All new connections are sent to "new_connection".    
    """
    global mongo_db

    logging.info(f"Starting websocket-server. Listens on port {port}")

    # mongo_client = AsyncIOMotorClient(f"mongodb://root:{MONGO_ROOT_PWD}@{MONGO_HOST}:27017")
    # mongo_db = mongo_client.db

    await websockets.serve(new_connection, port=port)        # Set up a websocket new_connections