import socketio
import os

sio = socketio.AsyncClient(logger=True, engineio_logger=False)
