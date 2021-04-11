# Cat Alarm 🙀

## Background

Ever had trouble with cats that 💩 in your garden..? 
You wish there was a way to scare them off while doing this ..? 
You have an ESP8266 microcontroller laying around and might consider investing in a small siren and a realy ..?

Then this project might be for you ✌🏻

## End results

Youtube video http://....

![cat_alarm_image](https://tva1.sinaimg.cn/large/008eGmZEgy1gpg2gav9fuj306y07ygll.jpg)



## How to use

Power on the device and search for the wifi network cat_alarm, then go to http://192.168.4.1
Within the interface you find

- **Enabled** - you can enable/disable the siren going of as you like (you may not want to wake up you neighbours)
- **Between hours** - you are able to configure within what hours you like this alarm to be active
- **Honk button** - there might be moment when you see that cat arrive then you can fire of the alarm when you like
- **Debug** - this will start the [webrepl](https://learn.adafruit.com/micropython-basics-esp8266-webrepl/access-webrepl) so you can remotely access the microcontroller
- **Configure** - when you like to configure which SSID this microcontroller should connect to, time when enabled and time it should "honk" etc

At the bottom you will get a list of the last motions that have been detected





## Build a frozen image from source and upload to ESP8266 

### Manually build binary image without upload 

Build the docker image of the master branch. The custom Dockerfile will add src as frozen and update the entrypoint

```bash
  docker build -t catalarm-build . && docker create --name catalarm-build-container catalarm-build && docker cp catalarm-build-container:/micropython/ports/esp8266/build-GENERIC/firmware-combined.bin firmware-combined.bin && docker stop catalarm-build-container && docker rm catalarm-build-container && docker rmi catalarm-build 
```

To specify a particular version of micropython provide it through the `build-arg`. Otherwise the HEAD of the master branch will be used.

```bash
  docker build -t catalarm-build --build-arg VERSION=v1.8.7 .
```

The firmware can then be uploaded with the esptool

```bash
  esptool.py --port ${SERIAL_PORT} --baud 115200 write_flash --verify --flash_size=detect 0 firmware-combined.bin
```

Here `${SERIAL_PORT}` is the path to the serial device on which the board is connected.

