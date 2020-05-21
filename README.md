Simple Python program to read the serial interface of a UNI-T UT61x
digital multimeter.

This program requires PySerial to be installed. This is typically done
with a command like the following:
```
apt-get install python-serial
```

The program is invoked with the serial port as argument. For example:
```
./read_dmm.py /dev/ttyUSB0
```

To place the UT61x in serial output mode, press and hold the REL
button on the multimeter for two seconds.

This program will automatically create a log file of the readings in a
file named `dmmlog-YYYYMMDD_HHMMSS.log`.

Unfortunately, the UT61x only sends updates once every ~582ms. The
screen on the multimeter actually updates faster than the serial
interface.
