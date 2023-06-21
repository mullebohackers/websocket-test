import os
import logging
import asyncio

from app import websocket_server
from http_server import http_server

"""
Environment
"""
DEBUG_MODE = os.getenv('DEBUG', "false") == "true"                       # Global DEBUG logging
LOGFORMAT = "%(asctime)s %(funcName)-10s [%(levelname)s] %(message)s"   # Log format
HTTP_SERVER_PORT = int(os.getenv('HTTP_SERVER_PORT',"8000"))
WEBSOCKET_SERVER_PORT = int(os.getenv('WEBSOCKET_SERVER_PORT',"8008"))


"""
MAIN function (starting point)
"""
def main():                 # noqa:E302
    # Enable logging. INFO is default. DEBUG if requested
    logging.basicConfig(level=logging.DEBUG if DEBUG_MODE else logging.INFO, format=LOGFORMAT)

    loop = asyncio.new_event_loop()         # Create an async loop
    # loop = asyncio.get_event_loop()         # Create an async loop

    websocket_runner = loop.create_task(websocket_server(WEBSOCKET_SERVER_PORT))
    http_runner = loop.create_task(http_server(HTTP_SERVER_PORT))        # Create http server # noqa:F841

    try:
        asyncio.set_event_loop(loop)        # Make the create loop the event loop
        loop.run_forever()                  # And run everything
    except (KeyboardInterrupt):             # Until somebody hits wants to terminate
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    main()
