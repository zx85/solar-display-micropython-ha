# Solis Cloud API display for ESP32

A version of a Solis Cloud API solar display using MicroPython and a [Cheap Yellow Display](https://github.com/witnessmenow/ESP32-Cheap-Yellow-Display)

It uses [PyScript](https://hacs-pyscript.readthedocs.io/en/latest/) to read data from the [Solis Sensor](https://github.com/hultenvp/solis-sensor/) HACS integration on Home Assistant and store it as JSON for the display to call in one go.


### Requirements
As the branch suggests, this needs Home Assistant to be installed, and a long lived access token (from your user profile at the bottom of the 'Security' tab)

It also needs PyScript to be installed - more on tha later.


## Hardware
Here's what I used to make my version:
- [Cheap Yellow Display - look for ESP32-2432S028R](https://www.google.com/search?q=ESP32-2432S028R)

It's around £10 and has everything I need.

## Software

### Loading the code

To get this working you'll first need to install MicroPython on your device. The instructions at [docs.micropython.org](https://docs.micropython.org/en/latest/esp32/tutorial/intro.html) are clear and easy to follow.

I use Microsoft [Visual Studio Code](https://code.visualstudio.com/) with the [Pymakr-preview](https://marketplace.visualstudio.com/items?itemName=pycom.pymakr-preview) extension installed (**note:** it's the preview version that, at time of writing, actually works. For some reason the standard version doesn't!)

It should be fairly straightforward to copy the code to the device.


### Configuring Home Assistant

You'll need to do the following:

#### Add the Solis integration
This can be found in the [HACS](https://hacs.xyz/) repository - details on how to set it up and configure it are [here](https://github.com/hultenvp/solis-sensor/).

#### Add the PyScript integration
This is another HACS integration - details are [here](https://hacs-pyscript.readthedocs.io/en/latest/)

#### Create a helper
Create a text helper called `input_text.solar_display_data`:

![create text helper](docs/solar-data-helper.png)


#### Copy the pyscript file
The `solar_data.py` file should be copied to the `homeassistant/pyscript` directory:

![pyscript directory](docs/pyscript-setup.png)

#### Create an automation that calls the pyscript service once every minute

This is done using 'Call Service' action

![solar data automation](docs/solar-data-automation.png)


### Libraries used
I made use of the following excellent libraries - and I'm grateful to the developers for making my life so much easier!

- Wifi Captive Portal - [github.com/anson-vandoren/esp8266-captive-portal](https://github.com/anson-vandoren/esp8266-captive-portal) - ([*blog post*](https://ansonvandoren.com/posts/esp8266-captive-web-portal-part-1/))
- Micropython library for ili9341 (including custom fonts) [github.com/rdagger/micropython-ili9341](https://github.com/rdagger/micropython-ili9341) - [*homepage*](https://www.rototron.info/)


### How it works

#### boot.py
The `boot.py` section generally deals with setting the credentials for the wifi network and Solis API. It loads a captive portal with an SSID starting `SolarDisplay-` and once you've connected to it with a handy device and web browser, you can enter the appropriate information there. Once it's done, it should reset and start displaying the data.

#### main.py
This runs a bunch of uasyncio loops, mainly to make web service calls to Solis every 45 seconds. While it's doing that, a dot appears around the middle of the bottom row of the screen. If it's successful, the dot disappears. If it's unsuccessful, it turns into two dots. 

The button on Pin 35 - if there is information available - prints the current daily solar generation, and the time of the last update by the datalogger (it only updates every five minutes). 

If there's been a problem with getting data, the last HTTP response code from solis cloud will be displayed, in order to help with diagnosis (for example, if the key/secret/id/serial combination are wrong, it'll return a 403).

The button on Pin 34 increases the brightness of the LED until it gets to maxium, then goes to 0

The button on Pin 36 is the hard reset button - hold it for 3 seconds and it clears the credentials and restarts at the captive portal.

Finally, the reset button does a normal reset on the ESP32, in case it's got stuck or something.


## 3D printed case

To follow..
