# networking-1006
INF1006 Computer Networks 2023/24 Trimester 2
Network Application Project Proposal
Group 19
Jonathan Lim (2300923), Felix Chang (2301105), Chew Liang Zhi (2300948), 
Ryan Oh (2300916), Darryl Ong (2301402), James Gonzales (2301136)

Smart Plant Monitoring System
Abstract
The Smart Plant Monitoring System provides users to monitor the conditions of their plants through a web dashboard. Conditions such as the soil moisture level, sunlight level, temperature and humidity. The dashboard also allows users to perform actions based on the conditions. Actions such as watering the plants, turning on the UV light and turning on the fan. The dashboard would also send a notification to notify users on the water tank level that is being used to water the plants.
Objective
Provide users with a Grafana Web Dashboard to monitor their plants and enable them to perform actions
Have 2x MQTT Client (Mosquitto MQTT) Raspberry Pis equipped with sensors and motors respectively to monitor the plants and perform actions
Have 1x MQTT Broker (Mosquitto and Node-RED) Raspberry Pi to receive and show the plant data on the Dashboard and send actions to Clients
Allow users to access the Dashboard from outside the network 
Timeline
Week 8: Project Proposal Discussion
Week 9: Testing of Sensors and Motors & Start of MQTT Implementation
Week 10: Continued work on Sensors and Motors & Implementing data onto the Dashboard
Week 11: Implementation and Testing of Clients & Brokers as a whole system
Week 12: Network configuration to allow access to Dashboard from outside
Week 13: Presentation Demo and Submission, Poster/3 Minute Video
Resources
3x Raspberry Pi 4 Model B, 1x Router, Online documentation for Mosquitto MQTT, Grafana (Web Dashboard), Node-RED (No-Code Development), and InfluxDB (Database Storage)
4x Sensors (UV Light, Temperature and Humidity, Ultrasonic, Moisture), 2x Motors (Water Pump, Light switch), Electrical Components (Breadboard, Wires, Resistors, etc.)
Workload Distribution

Client Team (Working with Sensors & Motors and Sending the Data):
Jonathan Lim (2300923), Felix Chang (2301105), Darryl Ong (2301402)

Server Team (Working with Dashboard, Receiving the Data, Parsing/Storing the Data):
James Gonzales (2301136), Chew Liang Zhi (2300948), Ryan Oh (2300916)
