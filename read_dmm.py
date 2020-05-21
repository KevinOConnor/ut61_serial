#!/usr/bin/env python
# Script to read and log data from a UNI-T UT61x multimeter
#
# Copyright (C) 2020  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import sys, time, select, optparse
import serial

FLAGS7 = {0x02: 'Hold', 0x04: 'Rel', 0x08: 'AC', 0x10: 'DC', 0x20: 'Autorange'}
FLAGS7_BAR = 0x01
FLAGS8 = { 0x04: 'Battery', 0x10: 'Min', 0x20: 'Max' }
FLAGS8_NANO = 0x02
FLAGS9 = { 0x04: 'Diode', 0x08: 'Buzzer' }
FLAGS9_PERCENT = 0x02
PREFIX = { 0x10: 'M', 0x20: 'k', 0x40: 'm', 0x80: 'u' }
UNIT = {
    0x01: 'degF', 0x02: 'degC', 0x04: 'F', 0x08: 'Hz',
    0x20: 'Ohm', 0x40: 'A', 0x80: 'V'
}
UNKNOWN_FLAGS = [0xc0, 0xc9, 0x01, 0x10]

class DMM:
    def __init__(self, infile, logfile):
        self.infile = infile
        self.logfile = logfile
        self.starttime = time.time()
        sys.stdout.write("\n")
        self.last_output = (0, 0)
    def report(self, msg):
        newlen = newcpos = len(msg)
        lastlen, curpos = self.last_output
        bs = '\x08' * curpos
        spaces = ''
        if lastlen > newlen:
            spaces = ' ' * (lastlen - newlen)
            newcpos = lastlen
        sys.stdout.write("%s%s%s" % (bs, msg, spaces))
        self.last_output = (newlen, newcpos)
        sys.stdout.flush()
    def parse_msg(self, msg):
        if len(msg) != 12 or msg[5] != ' ':
            return "Unknown: %s" % (repr(msg),)
        dpos = {'4': 4, '2': 3, '1': 2}.get(msg[6], 5)
        value = msg[:dpos] + '.' + msg[dpos:5]
        fbytes = [ord(b) for b in msg[7:11]]
        f7, f8, f9, f10 = fbytes
        flags = [flag for bit, flag in FLAGS7.items() if f7 & bit]
        flags += [flag for bit, flag in FLAGS8.items() if f8 & bit]
        flags += [flag for bit, flag in FLAGS9.items() if f9 & bit]
        flags += ["F%d=0x%02x" % (i+7, f & mask)
                  for i, (f, mask) in enumerate(zip(fbytes, UNKNOWN_FLAGS))
                  if f & mask]
        f11 = ord(msg[11])
        if f7 & FLAGS7_BAR or f11:
            rvalue = f11 & 0x7f
            sbyte = ''
            if f11 & 0x80:
                sbyte = '-'
            flags.append("Range %s%d" % (sbyte, rvalue))
        prefix = ''.join([p for bit, p in PREFIX.items() if f9 & bit])
        if f8 & FLAGS8_NANO:
            prefix += 'n'
        unit = ''.join([u for bit, u in UNIT.items() if f10 & bit])
        if f9 & FLAGS9_PERCENT:
            unit += '%'
        sflags = ''.join([" [%s]" % f for f in flags])
        return "%s%s%s%s" % (value, prefix, unit, sflags)
    def readserial(self):
        infile = self.infile
        leftover = ""
        while 1:
            # Read data
            try:
                res = select.select([infile], [], [], 2.0)
            except KeyboardInterrupt:
                sys.stdout.write("\n")
                return -1
            if not res[0]:
                self.report("")
                continue
            d = infile.read(4096)
            datatime = time.time()
            if not d:
                return 0

            # Find messages
            data = leftover + d
            msgs = data.split("\r\n")
            leftover = msgs.pop()
            for msg in msgs:
                fmsg = self.parse_msg(msg)
                delta = datatime - self.starttime
                self.logfile.write("%06.3f: %s\n" % (delta, fmsg))
                self.logfile.flush()
                self.report(fmsg)

def main():
    usage = "%prog <serialdevice>"
    opts = optparse.OptionParser(usage)
    options, args = opts.parse_args()
    if len(args) != 1:
        opts.error("Incorrect arguments")
    serialport = args[0]

    ser = serial.Serial(baudrate=2400, timeout=0)
    ser.rts = False
    ser.port = serialport
    ser.open()
    logname = time.strftime("dmmlog-%Y%m%d_%H%M%S.log")
    f = open(logname, 'w')
    dmm = DMM(ser, f)
    dmm.readserial()

if __name__ == '__main__':
    main()
