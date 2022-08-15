# IR rx/tx resources for Raspberry Pi Pico

Software for transmitting and receiving IR pulses in a non-blocking manner on a Raspberry Pi Pico, especially when the IR protocol is non-standard or unknown. 

You will require an appropriate IR LED hooked up to your Pico for transmission, and/or an IR receiver and demodulator for reception. If you're just using an IR receiver photocell, you'll need to demodulate the signal yourself (that is, convert the analog values from the photocell to a sequence of on/off digital values). You'll also need an extremely basic familiarity with Micropython (how to set it up on your Pico, import libraries, and the [machine.Pin](https://docs.micropython.org/en/latest/library/machine.Pin.html) class).

My primary intended use case for this project was:
1. Figure out the IR protocol used by my Roomba (which I believe is one of the 500 series ones)
2. Put together a small IR transmitter on a Pico to act as a Roomba virtual wall.

This software is more than sufficient for those goals! I'll update this repo with the script and circuit design once I've finished ironing out the hardware bugs.

However the IRReceive class can also be useful for decoding any other type of IR signal whose protocol is unknown, and both IRReceive and IRTransmit can be subclassed to target specific protocols. Expect to see an update for the 1998 Furby at some point...

## Credits

This code is heavily based on Peter Hinch's excellent [micropython_ir](https://github.com/peterhinch/micropython_ir) library and I encourage you to look there if you're working with standard IR protocols (NEC, Sony, Philips RC-5 and RC-6, etc). That library was simultaneously too general (works on multiple microcontrollers) and too specific (targeted at specific IR protocols) for my needs, so I ended up just stripping out the parts I needed and writing my own.

I've included the RP2_RMT driver from Peter Hinch's repository here directly in order to simplify importing/use; the docs for this class are [here](https://github.com/peterhinch/micropython_ir/blob/master/RP2_RMT.md).

## Use

Both receiver and transmitter are non-blocking, so in particular you can hook them both up to the same Pico board and use them simultaneously if you want.

### IRReceive

You can use IRReceive as-is and it will return a list of detected pulse lengths; you can also subclass it and override the `_decode` method to customise its behaviour for a specific IR protocol (e.g. see `IRReceiveRoomba`).

Example usage:

```
from pico_ir import ir_rx
from machine import Pin

ir_pin = Pin(16, Pin.IN)
test_rx = ir_rx.IRReceive(ir_pin, verbose=True)
test_rx.start(100)
```
Here my IR receiver (I'm using the [TSOP38238](https://www.adafruit.com/product/157)) is connected to pin 16 of the Pico; change this as needed to reflect your own setup.

Call `.start(n)` to start recording any IR pulses within range; the `n` indicates how many "edges" will be logged, that is how many changes low->high or high->low. 

It will time out and return the results after `10*n` milliseconds; note that it may record fewer than `n` edges (if not many changes in state were detected), and it will ignore any edges after the first `n` (even if it hasn't timed out yet).


### IRTransmit

You will need to subclass `IRTransmit` and override the `_create_tx` method to reflect your desired IR protocol: this should accept an integer value (the code to be transmitted) and convert it to an array of pulse lengths in microseconds.

Example usage (IRTransmitRoomba):

```
from pico_ir import ir_tx
from machine import Pin

led_pin = Pin(15, Pin.OUT, value=0)

test_tx = ir_tx.IRTransmitRoomba(led_pin)

test_tx.transmit(143, reps=10)
```

My IR LED is hooked up to pin 15; change this to reflect your own setup. This snippet would transmit the code `143` (which tells the Roomba to seek its dock) ten times.


## Links

- [Peter Hinch's micropython_ir repo](https://github.com/peterhinch/micropython_ir)
- [SB-Projects IR Remote Control Theory](https://www.sbprojects.net/knowledge/ir/): an excellent resource on how IR is used for remote controls and details on many common protocols.
- [iRobot Roomba Open Interface Spec](https://www.irobotweb.com/~/media/MainSite/PDFs/About/STEM/Create/iRobot_Roomba_600_Open_Interface_Spec.pdf?la=en): see page 26 for list of IR codes recognised by the Roomba.