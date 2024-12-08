from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
import yaml
from ai_handler import AIHandler
from utils.logger import setup_logger
import asyncio
import uvicorn
import sys
import signal
import threading
from datetime import datetime
import time
import os

app = FastAPI()
logger = setup_logger(debug=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global server instance
server = None

class GracefulShutdown:
    def __init__(self):
        self.should_exit = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        self.should_exit = True
        if server:
            logger.info("Shutting down server...")
            server.should_exit = True
            sys.exit(0)

shutdown_handler = GracefulShutdown()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}  # websocket_id: WebSocket
        self.ai_handlers: dict = {}  # websocket_id: AIHandler

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.ai_handlers:
            del self.ai_handlers[client_id]

    async def disconnect_all(self):
        for client_id in list(self.active_connections.keys()):
            await self.active_connections[client_id].close()
            self.disconnect(client_id)

    async def send_message(self, message: str, client_id: str, message_type: str = "ai"):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "type": message_type,
                "content": message
            })

manager = ConnectionManager()

class DebugManager:
    def __init__(self):
        self.debug_mode = False
        self.debug_messages = []
        self.max_messages = 100  # Keep last 100 debug messages

    def add_message(self, message: str, level: str = "DEBUG"):
        if self.debug_mode:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            debug_entry = {
                "timestamp": timestamp,
                "level": level,
                "message": message
            }
            self.debug_messages.append(debug_entry)
            if len(self.debug_messages) > self.max_messages:
                self.debug_messages.pop(0)
            logger.debug(f"{level}: {message}")

    def get_messages(self):
        return self.debug_messages

    def clear_messages(self):
        self.debug_messages = []

debug_manager = DebugManager()

@app.get("/", response_class=HTMLResponse)
async def get():
    with open("static/index.html") as f:
        return f.read()

@app.post("/shutdown")
async def shutdown():
    logger.info("Shutdown requested")
    await manager.disconnect_all()
    if server:
        # Force exit after response is sent
        threading.Thread(target=lambda: (time.sleep(1), os._exit(0))).start()
    return {"message": "Server shutting down"}

@app.post("/debug/toggle")
async def toggle_debug():
    debug_manager.debug_mode = not debug_manager.debug_mode
    status = "enabled" if debug_manager.debug_mode else "disabled"
    logger.info(f"Debug mode {status}")
    return {"status": status}

@app.get("/debug/messages")
async def get_debug_messages():
    return {"messages": debug_manager.debug_messages}

@app.post("/debug/clear")
async def clear_debug_messages():
    debug_manager.clear_messages()
    return {"status": "cleared"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    debug_manager.add_message(f"New client connected: {client_id}")
    
    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")
            debug_manager.add_message(f"Received command from {client_id}: {command}")
            
            if command == "init":
                service_type = data.get("service_type")
                debug_manager.add_message(f"Initializing {service_type} for client {client_id}")
                
                if service_type not in ["openai", "claude"]:
                    debug_manager.add_message(f"Invalid service type: {service_type}", "ERROR")
                    await manager.send_message("Invalid AI service type", client_id, "error")
                    continue
                
                try:
                    with open("config.yaml") as f:
                        config = yaml.safe_load(f)
                    
                    manager.ai_handlers[client_id] = AIHandler(config, service_type, logger)
                    debug_manager.add_message(f"AI handler created for {client_id}")
                    await manager.send_message(
                        f"Connected to {service_type.upper()} service", 
                        client_id, 
                        "system"
                    )
                except Exception as e:
                    debug_manager.add_message(f"Error initializing AI service: {str(e)}", "ERROR")
                    await manager.send_message(f"Error initializing AI service: {str(e)}", client_id, "error")
            
            elif command == "chat":
                if client_id not in manager.ai_handlers:
                    debug_manager.add_message(f"No AI handler for client {client_id}", "ERROR")
                    await manager.send_message("AI service not initialized", client_id, "error")
                    continue
                
                message = data.get("message", "").strip()
                debug_manager.add_message(f"Chat message from {client_id}: {message}")
                
                if message.lower() == '/clear':
                    manager.ai_handlers[client_id].clear_conversation()
                    debug_manager.add_message(f"Conversation cleared for {client_id}")
                    await manager.send_message("Conversation history cleared", client_id, "system")
                elif message:
                    response, model = manager.ai_handlers[client_id].get_ai_response(message)
                    debug_manager.add_message(f"AI ({model}) response: {response}")
                    debug_manager.add_message(f"AI response generated for {client_id}")
                    await manager.send_message(f"{model}: {response}", client_id, "ai")
            
    except WebSocketDisconnect:
        debug_manager.add_message(f"Client disconnected: {client_id}")
        manager.disconnect(client_id)

def run_server():
    global server
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, reload=False)
    server = uvicorn.Server(config)
    try:
        server.run()
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
    finally:
        # Ensure clean shutdown
        sys.exit(0)

if __name__ == "__main__":
    run_server() 