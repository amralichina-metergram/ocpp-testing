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

def validate_request_fields(request_message):
    required_fields = ["idTag"]
    payload = request_message[3] 
    for field in required_fields:
        if field not in payload:
            print(f"Validation failed: Missing required field '{field}'")
            return False
    print("Validation successful: All required fields are present.")
    return True

def validate_response_fields(response_message, ws):
    try:
        response = json.loads(response_message)
        
        if not isinstance(response, list) or len(response) < 3:
            print("Validation failed: Response is not a valid JSON array or does not have enough elements.")
            return False

        response_id = response[0] 
        if response_id != 3:
            print(f"Validation failed: Response message type is not 3.")
            return False

        payload = response[2]
        if not isinstance(payload, dict) or "idTagInfo" not in payload:
            print("Validation failed: Response payload is not valid or missing 'idTagInfo'.")
            ws.close()
            return False

        id_tag_info = payload["idTagInfo"]
        if id_tag_info.get("status") != "Accepted":
            print(f"Validation failed: Status is not 'Accepted', is '{id_tag_info.get('status')}'")
            ws.close()
            return False

        print("Response validation successful.")
        return True
    except json.JSONDecodeError:
        print("Validation failed: Response is not a valid JSON.")
        return False

def on_message(ws, message):
    print(f"Received response: {message}")
    if validate_response_fields(message,ws):
        ws.close()

def on_error(error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("Opened connection")
    
    if len(sys.argv) < 2:
        print("Usage: python Authorize.py <request_file>")
        sys.exit(1)
    
    request_file = sys.argv[1]
    authorize_req = load_request_message(request_file)
    
    print(f"Request message loaded: {authorize_req}")

    if not validate_request_fields(authorize_req):
        print("Invalid request message format.")
        ws.close()
        return
    
    ws.send(json.dumps(authorize_req))
    print("Sent Authorize request")

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
