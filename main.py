from fastapi import FastAPI
import os
import socketio
import uvicorn
import asyncio

from chess.chess_tracker import ChessTracker
from chess.window_hook import get_foreground_event_observer
from flask_util import create_routing_hash, load_json

HASH_PATH = os.path.join(os.getcwd(), '../assets/unique_hash.json')
NOTATION_DIR_PATH = os.path.join(os.getcwd(), '../assets/notation')

if not os.path.exists(HASH_PATH):
    create_routing_hash(HASH_PATH)

hash_data = load_json(HASH_PATH)
if hash_data['routing_hash'] is None:
    create_routing_hash(HASH_PATH)
    hash_data = load_json(HASH_PATH)

unique_hash = hash_data['routing_hash']

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = FastAPI()
socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path=f"{unique_hash}.io")
chess_tracker_obj = ChessTracker()
get_foreground_event_observer(chess_tracker_obj)()

@sio.event
async def connect(sid, environ):
    await sio.emit('server_response', {'status': 200}, room=sid)

@sio.event
async def start(sid, data):
    chess_tracker_obj.set_app_state(data['app_state'])
    chess_board_coords = await asyncio.to_thread(chess_tracker_obj.find_chess_board)

@sio.event
async def change_state(sid, data):
    chess_tracker_obj.set_app_state(data['app_state'])

@sio.event
async def disconnect(sid):
    pass

if __name__ == '__main__':
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
