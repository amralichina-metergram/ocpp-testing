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

def load_request_messages(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def validate_request_fields(request_message):
    message_type = request_message[2]
    
    if message_type == "BootNotification":
        required_fields = ["chargePointVendor", "chargePointModel"]
    elif message_type == "Authorize":
        required_fields = ["idTag"]
    elif message_type == "StartTransaction":
        required_fields = ["connectorId", "idTag", "meterStart", "timestamp"]
    else:
        required_fields = [] 

    payload = request_message[3]
    for field in required_fields:
        if field not in payload:
            print(f"Validation failed: Missing required field '{field}'")
            return False
        if not isinstance(payload[field], str) and field != "connectorId" and field != "meterStart":
            print(f"Validation failed: Field '{field}' is not a string.")
            return False
    print(f"{message_type} validation successful.")
    return True

def validate_response_fields(ws, response_message):
    try:
        print(f"Raw response received: {response_message}")
        response = json.loads(response_message)

        if not isinstance(response, list):
            print("Validation failed: Response is not a valid JSON array.")
            return False
        
        if len(response) < 3:
            print("Validation failed: Response array does not have enough elements.")
            return False
        
        payload = response[2]

        if ws.expected_type == "BootNotification":
            if payload.get("status") != "Accepted":
                print(f"Validation failed: Status is not 'Accepted', but '{payload.get('status')}'")
                return False
            if payload.get("interval") != 900:
                print(f"Validation failed: Interval is not 900, but '{payload.get('interval')}'")
                return False
        elif ws.expected_type == "Authorize":
            if payload.get("idTagInfo", {}).get("status") != "Accepted":
                print(f"Validation failed: idTagInfo status is not 'Accepted', but '{payload.get('idTagInfo', {}).get('status')}'")
                return False
            ws.saved_idTag = ws.current_request[3].get("idTag")
        elif ws.expected_type == "StartTransaction":
            if payload.get("idTagInfo", {}).get("status") != "Accepted":
                print(f"Validation failed: idTagInfo status is not 'Accepted', but '{payload.get('idTagInfo', {}).get('status')}'")
                return False
            if ws.saved_idTag != ws.current_request[3].get("idTag"):
                print(f"Validation failed: idTag in StartTransaction does not match the saved idTag from Authorize.")
                return False

        print(f"{ws.expected_type} response validation successful.")
        return True
    except json.JSONDecodeError as e:
        print(f"Validation failed: JSON parsing error - {str(e)}")
        return False

def on_message(ws, message):
    print(f"Received response: {message}")
    validate_response_fields(ws, message)
    ws.current_request_index += 1

    if ws.current_request_index < len(ws.request_messages):
        send_next_request(ws)
    else:
        print("All messages processed. Closing connection.")
        ws.close()

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("Connection closed")

def on_open(ws):
    print("Opened connection")
    
    if len(sys.argv) < 2:
        print("Usage: python flow.py <request_file>")
        sys.exit(1)
    
    request_file = sys.argv[1]
    ws.request_messages = load_request_messages(request_file)
    ws.current_request_index = 0
    ws.saved_idTag = None
    send_next_request(ws)

def send_next_request(ws):
    current_request = ws.request_messages[ws.current_request_index]
    print(f"Sending request: {current_request}")

    if validate_request_fields(current_request):
        ws.expected_type = current_request[2]
        ws.current_request = current_request
        ws.send(json.dumps(current_request))
    else:
        print(f"Invalid request message format for {current_request[2]}. Skipping.")
        ws.close()
        sys.exit(1)

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