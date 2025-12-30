import asyncio
import websockets
import json

# Replace with your ESP32 IP address
ESP32_IP = "localhost" 
URI = f"ws://{ESP32_IP}:8080"

async def test_mcp_server():
    print(f"Connecting to {URI}...")
    try:
        async with websockets.connect(URI) as websocket:
            print("Connected!")
            
            # 1. Initialize
            print("\n--- Sending Initialize ---")
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "test-client", "version": "1.0"}
                }
            }
            await websocket.send(json.dumps(init_req))
            resp = await websocket.recv()
            print(f"Response: {resp}")

            # 2. List Tools
            print("\n--- Sending Tools List ---")
            list_req = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            await websocket.send(json.dumps(list_req))
            resp = await websocket.recv()
            print(f"Response: {resp}")
            
            # 3. Call Tool (Turn On)
            print("\n--- Calling set_lamp (ON) ---")
            call_req = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "set_lamp",
                    "arguments": {"state": True}
                }
            }
            await websocket.send(json.dumps(call_req))
            resp = await websocket.recv()
            print(f"Response: {resp}")
            
            # 4. Call Tool (Turn Off)
            print("\n--- Calling set_lamp (OFF) ---")
            call_req["id"] = 4
            call_req["params"]["arguments"]["state"] = False
            await websocket.send(json.dumps(call_req))
            resp = await websocket.recv()
            print(f"Response: {resp}")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the ESP32 is powered on, connected to WiFi, and the IP address in this script is correct.")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
