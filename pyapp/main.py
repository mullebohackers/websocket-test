import os
import logging
import signal
import asyncio

from app import websocket_server
from http_server import http_server

"""
Environment
"""
DEBUG_MODE = os.getenv('DEBUG', "false") == "true"                       # Global DEBUG logging
LOGFORMAT = "%(asctime)s %(funcName)-10s [%(levelname)s] %(message)s"   # Log format
WEBSOCKET_SERVER_PORT = int(os.getenv('WEBSOCKET_SERVER_PORT',"8008"))
HTTP_SERVER_PORT = int(os.getenv('HTTP_SERVER_PORT',"8000"))
HTTP_STATIC_DIR = os.getenv('HTTP_STATIC_DIR', "./jsapp/out")

"""
MAIN function (starting point)
"""
async def main():                 # noqa:E302
    loop = asyncio.get_running_loop()
    
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    websocket_runner = loop.create_task(websocket_server(WEBSOCKET_SERVER_PORT))
    http_runner = loop.create_task(http_server(HTTP_SERVER_PORT, HTTP_STATIC_DIR))        # Create http server # noqa:F841

    await stop      # Run forever until stopped!

if __name__ == "__main__":
    # Enable logging. INFO is default. DEBUG if requested
    logging.basicConfig(level=logging.DEBUG if DEBUG_MODE else logging.INFO, format=LOGFORMAT)

    asyncio.run(main())     # Start an async loop and run main
