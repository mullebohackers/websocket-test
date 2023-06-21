import os
import logging

from aiohttp import web



""" 
HTTP root handler
"""
async def root_handler(request):
    return web.HTTPFound('/index.html')


""" 
HTTP server setup
"""
async def http_server(port:int):
    logging.info(f"Starting HTTP-server. Listens on / on port {port}")

    app = web.Application()
    app.router.add_route('*', '/', root_handler)
    app.router.add_static('/', './jsapp/build')
    runner = web.AppRunner(app)

    await runner.setup()
    site = web.TCPSite(runner, port=port)
    await site.start()

    return runner
