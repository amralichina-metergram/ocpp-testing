import websocket
import json
import sys
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('..', '.env')
load_dotenv(dotenv_path=env_path)

url = os.getenv('WEBSOCKET_URL')
socketProtocol = os.getenv('SEC_WEB_SOCKET_PROTOCOL')

def load_request_message(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def validate_response_fields(response_message):
    try:
        response = json.loads(response_message)

        if not isinstance(response, list):
            print("Validation failed: Response is not a valid JSON array.")
            return False
        
        if len(response) < 3:
            print("Validation failed: Response array does not have enough elements.")
            return False
        
        payload = response[2]

        if not isinstance(payload, dict):
            print("Validation failed: Payload is not a valid JSON object.")
            return False
        
        if "currentTime" not in payload:
            print("Validation failed: 'currentTime' is missing in response payload.")
            return False

        print("Response validation successful.")
        return True
    except json.JSONDecodeError:
        print("Validation failed: Response is not a valid JSON.")
        return False

def on_message(ws, message):
    print(f"Received response: {message}")
    if validate_response_fields(message):
        ws.close()

def on_error(error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("Opened connection")
    
    if len(sys.argv) < 2:
        print("Usage: python script.py <request_file>")
        sys.exit(1)
    
    request_file = sys.argv[1]
    request_message = load_request_message(request_file)
    
    print(f"Request message loaded: {request_message}")

    ws.send(json.dumps(request_message))
    print("Sent request")

def run_websocket_client():
    ws = websocket.WebSocketApp(
        url,  
        header={"Sec-WebSocket-Protocol": socketProtocol}, 
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    ws.run_forever()  

if __name__ == "__main__":
    run_websocket_client()
