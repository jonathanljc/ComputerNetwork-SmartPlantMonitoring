# 🌱 Smart Plant Monitoring System

## 📄 Project Overview
The **Smart Plant Monitoring System** is an IoT-based project developed for **INF1006 Computer Networks**. It uses **Raspberry Pi 4**, **MQTT**, and **Node-RED** to monitor and control environmental conditions for plants. The system provides real-time data via a **web dashboard** and allows automated actions like watering and controlling LED light intensity.

---

## 🔧 System Features

### 🛠 Monitoring
- **Soil Moisture Level**  
- **UV Light Intensity**  
- **Temperature & Humidity**  

### 💡 Dashboard
- Real-time monitoring via Node-RED web dashboard.  
- Perform automated actions such as:
  - **Watering plants** using a submersible pump.  
  - **Controlling light intensity** using LEDs.  

---

## 📁 Project Structure
The project contains two key components:

1. **Broker**:
   - Runs the **Mosquitto MQTT broker** to manage communication between devices.
   - Includes the Node-RED server for real-time visualization.

2. **Client**:
   - Two separate clients, **Client A** and **Client B**, running on Raspberry Pis:
     - **Client A** (`piClient1.py`): Handles soil moisture and ultrasonic sensors.
     - **Client B** (`piClient2.py`): Handles temperature, humidity, and UV light sensors.

---

# 🚀 Installation Guide

For detailed installation instructions, refer to the respective README files:

- **Broker Setup**: [Broker Folder README](https://github.com/jonathanljc/ComputerNetwork-SmartPlantMonitoring/blob/main/broker/readme.md)  
- **Client Setup**: [Client Folder README](https://github.com/jonathanljc/ComputerNetwork-SmartPlantMonitoring/blob/main/client/readme.md)  

---

## 📦 Resources Used

### Hardware:
- 3x Raspberry Pi 4 Model B  
- Soil Moisture Sensor  
- UV Sensor  
- DHT11 (Temperature & Humidity)  
- Submersible Water Pump  
- LEDs  
- Ultrasonic Sensor  

### Software:
- MQTT (Mosquitto Broker)  
- Node-RED  
- Python (Paho-MQTT, Adafruit Libraries)  

---

## 📹 Demonstration Video

Watch the project demonstration here:  
[**Smart Plant Monitoring System Demo**](#)

---

## 🎓 Contributors

**Group 19**:  

| **Name**          | **ID**       | **Email**                          |
|-------------------|--------------|------------------------------------|
| Jonathan Lim      | 2300923      | 2300923@sit.singaporetech.edu.sg   |
| Felix Chang       | 2301105      | 2301105@sit.singaporetech.edu.sg   |
| Chew Liang Zhi    | 2300948      | 2300948@sit.singaporetech.edu.sg   |
| Ryan Oh           | 2300916      | 2300916@sit.singaporetech.edu.sg   |
| Darryl Ong        | 2301402      | 2301402@sit.singaporetech.edu.sg   |
| James Gonzales    | 2301136      | 2301136@sit.singaporetech.edu.sg   |

---


