## Build a frozen image from source and upload to ESP8266 <a name="BuildFroze"></a>

### Manually build binary image without upload <a name="ManualBuild"></a>

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

