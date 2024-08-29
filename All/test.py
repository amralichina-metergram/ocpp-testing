import websocket
import json
import sys
import os
from dotenv import load_dotenv
from pathlib import Path
import datetime
import time  

env_path = Path('..', '.env')
load_dotenv(dotenv_path=env_path)

url = os.getenv('WEBSOCKET_URL')
socketProtocol = os.getenv('SEC_WEB_SOCKET_PROTOCOL')

def load_request_messages(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def validate_status_notification_request(payload):
    required_fields = ["connectorId", "errorCode", "status", "timestamp"]
    allowed_error_codes = [
        "ConnectorLockFailure", "EVCommunicationError", "GroundFailure",
        "HighTemperature", "InternalError", "LocalListConflict", "NoError"
    ]
    allowed_statuses = [
        "Available", "Preparing", "Charging", "SuspendedEVSE", "SuspendedEV",
        "Finishing", "Reserved", "Unavailable", "Faulted"
    ]

    for field in required_fields:
        if field not in payload:
            print(f"Validation failed: Missing required field '{field}'")
            return False
        
        if field == "errorCode" and payload[field] not in allowed_error_codes:
            print(f"Validation failed: Invalid errorCode '{payload[field]}'")
            return False
        
        if field == "status" and payload[field] not in allowed_statuses:
            print(f"Validation failed: Invalid status '{payload[field]}'")
            return False

    print("StatusNotification request validation successful.")
    return True    

def validate_request_fields(request_message):
    message_type = request_message[2]
    payload = request_message[3]
    
    if message_type == "BootNotification":
        required_fields = ["chargePointVendor", "chargePointModel"]
    elif message_type == "Authorize":
        required_fields = ["idTag"]
    elif message_type == "HeartBeat":
        required_fields = [];      
    elif message_type == "StartTransaction":
        required_fields = ["connectorId", "idTag", "meterStart", "timestamp"]
    elif message_type == "StatusNotification":
        return validate_status_notification_request(payload);
    elif message_type == "StopTransaction":
        required_fields = ["idTag", "meterStop", "timestamp", "transactionId"]
    elif message_type == "MeterValues":
        required_fields = ["connectorId", "meterValue"]                
    else:
        required_fields = [] 

    payload = request_message[3]
    for field in required_fields:
        if field not in payload:
            print(f"Validation failed: Missing required field '{field}'\n")
            return False
    
    print(f"{message_type} validation successful.")
    return True

def validate_response_fields(ws, response_message):
    try:
        #print(f"Raw response received: {response_message}")
        response = json.loads(response_message)

        if not isinstance(response, list):
            print("Validation failed: Response is not a valid JSON array.\n")
            return False
        
        if len(response) < 3:
            print("Validation failed: Response array does not have enough elements.\n")
            return False
        
        payload = response[2]

        if ws.expected_type == "BootNotification":
            if payload.get("status") != "Accepted":
                print(f"Validation failed: Status is not 'Accepted', is '{payload.get('status')}'\n")
                return False
            if payload.get("interval") != 900:
                print(f"Validation failed: Interval is not 900, but '{payload.get('interval')}'\n")
                return False
        elif ws.expected_type == "Authorize":
            if payload.get("idTagInfo", {}).get("status") != "Accepted":
                print(f"Validation failed: idTagInfo status is not 'Accepted', but '{payload.get('idTagInfo', {}).get('status')}'\n")
                return False
            ws.saved_idTag = ws.current_request[3].get("idTag")
        elif ws.expected_type == "HeartBeat":
            if "currentTime" not in payload:
               print("Validation failed: Not received valid response. Missing 'currentTime' in HeartBeat response.\n")
               return False
        elif ws.expected_type == "StartTransaction":
            if payload.get("idTagInfo", {}).get("status") != "Accepted":
                print(f"Validation failed: idTagInfo status is not 'Accepted', is '{payload.get('idTagInfo', {}).get('status')}'\n")
                return False
            if ws.saved_idTag != ws.current_request[3].get("idTag"):
                print(f"Validation failed: idTag in StartTransaction does not match the saved idTag from Authorize.\n")
                return False
            if "transactionId" not in payload:
                print(f"Validation failed: Missing transactionId in StartTransaction response.\n")
                return False
            ws.saved_transactionId = payload["transactionId"]
            #Validate connectorId ToDo
            
        elif ws.expected_type == "StatusNotification":
            if payload != {}:
                print(f"Validation failed: StatusNotification response should be empty, but got {payload}.\n")
                return False
        elif ws.expected_type == "StopTransaction":
            if payload.get("errorCode") == 6 and payload.get("ErrorDescription") == "Invalid payload for StopTransaction message":
                print(f"Validation failed: {payload}\n")
                return False 
        elif ws.expected_type == "MeterValues":
            if payload.get("Status") != "Accepted":
                print(f"Validation failed: Status is not 'Accepted', is '{payload.get('status')}'\n")
                return False
            if ws.saved_transactionId != ws.current_request[3].get("transactionId"):
                print(f"Validation failed: transactionId in MeterValues does not match transactionId from StartTransaction.\n")
                return False
            time.sleep(20)   

            # Validate connectorId ToDo     
                
        print(f"{ws.expected_type} response validation successful.\n")
        return True
    except json.JSONDecodeError as e:
        print(f"Validation failed: JSON parsing error - {str(e)}\n")
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
    ws.saved_transactionId = None
    ws.saved_timestamp = None
    ws.current_time = None
    send_next_request(ws)

def send_next_request(ws):
    current_request = ws.request_messages[ws.current_request_index]

    if current_request[2] == "StartTransaction":
        ws.current_time = datetime.datetime.now() - datetime.timedelta(hours=2)
        current_request[3]["timestamp"] = ws.current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + '7254'+ 'Z'
        ws.saved_timestamp = current_request[3]["timestamp"]

    if current_request[2] == "MeterValues":    
        if ws.saved_transactionId is None:
            print("Error: Missing transactionId for MeterValues request.")
            return
        
        current_request[3]["transactionId"] = ws.saved_transactionId
    
        if ws.saved_timestamp is None:
            print("Error: Missing timestamp for MeterValues request.")
            return

        timestamp_dt = datetime.datetime.fromisoformat(ws.saved_timestamp.replace("Z", "+00:00"))
    
        new_timestamp_dt = timestamp_dt + datetime.timedelta(minutes=1)
    
        new_timestamp = new_timestamp_dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + "Z"
    
        current_request[3]["meterValue"][0]["timestamp"] = new_timestamp

        ws.saved_timestamp = new_timestamp

        
    if current_request[2] == "StopTransaction":
        if ws.saved_transactionId is None:
            print(f"Error: Missing transactionId for StopTransaction request.")
            return
        
        current_request[3]["transactionId"] = ws.saved_transactionId         

    print(f"Sending request: {current_request}")

    if validate_request_fields(current_request):
        ws.expected_type = current_request[2]
        ws.current_request = current_request
        ws.send(json.dumps(current_request))

    else:
        ws.current_request_index += 1
        if ws.current_request_index < len(ws.request_messages):
            send_next_request(ws)   

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