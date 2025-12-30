import asyncio
import json
import logging
import os
from websockets.server import serve
from gpiozero import LED, Device
from gpiozero.pins.mock import MockFactory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Hardware Setup
LAMP_PIN = 17 # GPIO 17

# Check if running on Pi, otherwise use Mock
try:
    # Try to access a pin to see if we are on a Pi or have GPIO access
    # reliable check for Pi is checking /proc/cpuinfo or just try/except on Pin access if full gpiozero isn't checking yet
    # simpler: just rely on gpiozero's default behavior, or force Mock if env var set
    if os.environ.get("GPIOZERO_PIN_FACTORY") == 'mock' or os.name == 'nt' or os.uname().sysname == 'Darwin':
        logger.info("Using Mock GPIO Factory")
        Device.pin_factory = MockFactory()
    
    lamp = LED(LAMP_PIN)
except Exception as e:
    logger.warning(f"Failed to initialize GPIO: {e}. Falling back to Mock.")
    Device.pin_factory = MockFactory()
    lamp = LED(LAMP_PIN)

# Tools definition
TOOLS = {
    "set_lamp": {
        "description": "Control the Minecraft Lamp (turn on or off)",
        "inputSchema": {
            "type": "object", 
            "properties": {
                "state": {"type": "boolean", "description": "True to turn on, False to turn off"}
            }, 
            "required": ["state"]
        }
    },
    "get_lamp": {
        "description": "Get the current state of the lamp",
        "inputSchema": {
            "type": "object", 
            "properties": {}
        }
    }
}

async def handle_set_lamp(args):
    if "state" not in args:
        return {"isError": True, "content": [{"type": "text", "text": "Missing 'state' argument"}]}
    
    state = args["state"]
    if state:
        lamp.on()
        msg = "Lamp turned ON"
    else:
        lamp.off()
        msg = "Lamp turned OFF"
        
    logger.info(f"Tool set_lamp called: {msg}")
    return {
        "isError": False,
        "content": [{"type": "text", "text": msg}]
    }

async def handle_get_lamp(args):
    state = "ON" if lamp.is_lit else "OFF"
    logger.info(f"Tool get_lamp called: {state}")
    return {
        "isError": False,
        "content": [{"type": "text", "text": state}]
    }

async def process_request(message):
    try:
        data = json.loads(message)
    except json.JSONDecodeError:
        return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}

    if data.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": data.get("id")}

    method = data.get("method")
    req_id = data.get("id")
    params = data.get("params", {})

    response = {"jsonrpc": "2.0", "id": req_id}

    if method == "initialize":
        response["result"] = {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "pi-mcp-lamp", "version": "1.0.0"}
        }
    
    elif method == "tools/list":
        tools_list = []
        for name, defn in TOOLS.items():
            tools_list.append({
                "name": name,
                "description": defn["description"],
                "inputSchema": defn["inputSchema"]
            })
        response["result"] = {"tools": tools_list}
        
    elif method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        
        if name == "set_lamp":
            result = await handle_set_lamp(args)
            if result.get("isError"):
                response["error"] = {"code": -32602, "message": result["content"][0]["text"]}
            else:
                response["result"] = result
        elif name == "get_lamp":
            result = await handle_get_lamp(args)
            response["result"] = result
        else:
            response["error"] = {"code": -32601, "message": "Tool not found"}
            
    elif method == "notifications/initialized":
        # No response needed for notifications
        return None
        
    else:
        response["error"] = {"code": -32601, "message": "Method not found"}

    return response

async def handler(websocket):
    async for message in websocket:
        logger.info(f"Received: {message}")
        response = await process_request(message)
        if response:
            resp_str = json.dumps(response)
            logger.info(f"Sending: {resp_str}")
            await websocket.send(resp_str)

async def main():
    logger.info("Starting MCP Server on 0.0.0.0:8080...")
    async with serve(handler, "0.0.0.0", 8080):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
