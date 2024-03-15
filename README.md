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
   3. Replace `localhost` with IP of Raspberry PI.
      1. Try `hostname -I`
5. In nodered, install dependencies.
   1. `@flowfuse/node-red-dashboard`
   2. `node-red-node-sqlite`