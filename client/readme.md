# Installation for Both Raspberry PIs

1. Update your Raspberry PI.
   1. `sudo apt update`
   2. `sudo apt upgrade`
2. Install the MQTT package.
   1. `sudo apt install mosquitto mosquitto-clients`

# Installation for Client A
1. Copy `piClient1.py` and `piClient1-requirements.txt` into the pi.
2. Create a new virtual environment.
   1. `python -m venv venv` or `python3 -m venv venv`
3. Activate the virtual environement.
   1. `source venv/bin/activate`
4. Install dependencies.
   1. `pip install -r piClient1-requirements.txt`
5. Run the script.
   1. `python piClient1.py` or `python3 piClient1.py`


# Installation for Client B
1. Copy `piClient2.py` into the pi.
2. Create a new virtual environment.
   1. `python -m venv venv` or `python3 -m venv venv`
3. Activate the virtual environement.
   1. `source venv/bin/activate`
4. Install dependencies.
   1. `sudo apt-get install libgpiod2`
   2. `pip install adafruit-circuitpython-dht adafruit-blinka adafruit-circuitpython-ltr390`
5. Run the script.
   1. `python piClient1.py` or `python3 piClient1.py`