# Installation

1. Update your Raspberry PI.
   1. `sudo apt update`
   2. `sudo apt upgrade`
2. Install the MQTT package.
   1. `sudo apt install mosquitto mosquitto-clients`
3. Install the nodered package.
   1. https://nodered.org/docs/getting-started/raspberrypi
4. Run nodered locally.
   1. `node-red-pi --max-old-space-size=256`
   2. Frontend running on `http://localhost:1880`
      1. Replace `localhost` with IP of Raspberry PI.
      2. Find the IP of the PI using `hostname -I`
5. In the nodered palette, install dependencies.
   1. `@flowfuse/node-red-dashboard`
6. Copy and paste the entire text in flows.json into nodered import window.
7. In the production tab, change the following:
   1. Server of `sensor/capacity` changed to IP of client running piClient1.py
   2. Server of `sensor/moisture` changed to IP of client running piClient1.py
   3. Server of `relay/water` changed to IP of client running piClient1.py
   4. Server of `home/sensorsF` changed to IP of client running piClient12.py
8. Deploy the changes.
9. Dashboard running on `http://localhost/dashboard/page1`
   1. Replace `localhost` with IP of Raspberry PI.
