# PyonAir

PyonAir is a low-cost open-source air pollution monitor developed at the University of Southampton. The monitor measures particulate matter (PM), temperature, and humidity. It also associates the readings with location pulled from GPS.

![PyonAir](https://blobscdn.gitbook.com/v0/b/gitbook-28427.appspot.com/o/assets%2F-LheWV6hCRaax90oq84D%2F-LixJBNfaAPa5rYwP1p_%2F-LixJEjxsWOdrSaRS4OQ%2FCAD%20pic%202.jpg?alt=media&token=b29deb3e-967f-48d5-8073-85b7d377e322)

## Hardware

All the hardware components used for the air monitor are listed [here](https://s-u-pm-sensor.gitbook.io/instructions/hardware/hardware-overview).

## Wiring

There are three options to wire the device:
1. custom made PCB (schematic in the link below)
2. breadboard
3. stripboard

The wiring instructions can be found [here](https://s-u-pm-sensor.gitbook.io/instructions/tutorial/wiring).

## Getting Started

After wiring all the components, next step is to setup the software. If you already have the latest version of the firmware on your LoPy, drivers, and development environment for Pycom boards, you can skip to [Installation](#installation).

### Prerequisites

Follow the instructions on https://docs.pycom.io/gettingstarted/installation/ to setup your device and your development environment.

### Installation

1. Pull the repository using:

    ```
    git clone https://github.com/pyonair/PyonAir-pycom.git
    ```
    
    or alternatively use [GitHub Desktop](https://desktop.github.com/) to clone the repository.
    
2. Connect your LoPy with a USB cable to your machine and open the repository in your editor (Atom or VSC) with Pymakr plugin enabled. Connect to your device with Pymakr. In case of issues, please refer to: https://docs.pycom.io/pymakr/installation/

3. When connected, hit the upload button to flash the code into your LoPy.

Congratulations! You are now setup and ready to configure your device 😎

### Configuration

When configuring the device for the first time, it should automatically switch itself into configuration mode, indicated by continuous blue light. The device creates a WiFi AP named NewPyonAir, the password is _newpyonair_. After connecting your machine or phone to its WiFi, in your browser, navigate to http://192.168.4.10. The configuration page will show up. After filling all the values and pressing _Save_, the device will reboot, initialise itself (amber light finished with green blink), and continue running according the configuration.

If required to reconfigure the device, simply hold the button for 3 seconds, which enters the configuration mode (constant blue light), then follow the steps above.

### Debugging

* Once the device is plugged, it starts initialisation, which is indicated by **amber light**.
* Successful initialisation is indicated by **green light blinking twice**
* **Red light blinking** immediately after boot indicates an issue with SD Card (perhaphs it is not plugged in or is not formatted correctly) or an issue with the [Real Time Clock](https://s-u-pm-sensor.gitbook.io/instructions/hardware/hardware-overview/ds3231-real-time-clock). This error will not be logged into a logging file; however, it still can be seen in Pymakr's REPL if the LoPy is connected to your machine.
* **Red light flashing during initialisation** indicates an issue somewhere else. This issue will be logged into _status_log.txt_ file saved on the SD Card. This error can also be seen in Pymakr's REPL after connecting LoPy to your machine.
* **Red blinks** during normal operation indicates runtime errors. 

If there are any issues, please report them on [GitHub Issues](https://github.com/pyonair/PyonAir-pycom/issues).

## Built With/Using

* [MicroPython](https://micropython.org/)
* [Pycom](https://pycom.io/)
* [LoRaWAN](https://www.thethingsnetwork.org/docs/lorawan/)

## Contributing

You can submit your fixes/features via [Pull requests](https://github.com/pyonair/PyonAir-pycom/pulls), alternatively contact one of the developers/supervisors.

## Credits

Project supervised by [Dr Steven J Johnston](https://www.southampton.ac.uk/engineering/about/staff/ferrang.page).
Special thanks to [Dr Steven J Johnston](https://www.southampton.ac.uk/engineering/about/staff/ferrang.page), [Dr Philip J Basford](https://www.southampton.ac.uk/engineering/about/staff/pjb1u12.page), and [Florentin Bulot](https://www.southampton.ac.uk/smmi/about/our_students/florentin-bulot.page) for advice, insights, and help with debugging.

## Authors

* **[Daniel Hausner](https://github.com/danhaus)** - *Initial work & software development*
* **[Peter Varga](https://github.com/pe-varga)** - *Initial work & software development*
* **[Hazel Mitchell](https://github.com/CeruleanMars)** - *Initial work & hardware*

See also the list of [contributors](https://github.com/pyonair/PyonAir-pycom/graphs/contributors) who participated in this project.

## License

To be added.
