# OCPP WebSocket Testing Project
## **1. Clone the Project**

To get started with the project, first clone the [project repository](https://github.com/nikolastojkovski-metergram/internship-ocpp)

### **1.1 Connect to the Database**

Ensure that you have connected to the database as required by the project.

### **1.2 Run the Project**

Before proceeding, make sure that the project runs successfully. Verify that all necessary configurations and dependencies are set up correctly.

## 2. Clone the Repository
To start working with this project and perform WebSocket client testing in Python, clone the repository using the following command:

    git clone https://github.com/amralichina-metergram/ocpp-testing.git

2.1 Install Dependencies
Navigate to the project directory and install the [WebSocket client library](https://pypi.org/project/websocket-client/):

 On macOS/Linux:
 
    pip install websocket-client
    
On Windows:

    pip install websocket-client
    
2.2 Running the Code Examples
For testing using the WebSocket client, you will need to execute Python scripts with specific JSON files.

Example for BootNotification

Navigate to the BootNotification directory:

On macOS/Linux:
    
      cd BootNotification
      
On Windows:
    
      cd BootNotification
Run the script with a valid JSON file:

On macOS/Linux:

     python BootNotification.py boot_notification_valid.json
      
On Windows:

    py BootNotification.py boot_notification_valid.json
      
Running Other Scripts

The format for running other scripts is as follows:

On macOS/Linux:

      python nameOfFile.py nameOfFile.json
On Windows:

      py nameOfFile.py nameOfFile.json
Replace nameOfFile.py with the name of your Python script and nameOfFile.json with the corresponding JSON file.

In the .py files, you are connecting to the WebSocket and performing testing, while the .json files contain the request messages.

## 3. Notes

   Ensure that you have Python installed on your system.
   Make sure to follow any additional setup instructions provided in the project or script documentation.

Happy testing!
