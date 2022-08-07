from machine import Timer, Pin
from utime import ticks_us, ticks_diff

class Receive():
  def __init__(self, pin, max_edges=250):
    self.pin = pin
    self.edge = 0
    self.max_edges = max_edges
    self.times = [None for i in range(self.max_edges)]
    self.tim = Timer(-1)
    self.cleanup = self.decode  # this should take one argument, which is the timer object
    pin.irq(handler=self.pin_cb, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)  # sets up the interrupt on the pin and calls the handler fn when triggered

  def pin_cb(self, pin):
    # pin callback should take one argument which is the pin
    # but we don't actually need it
    t = ticks_us()  # gets the timer value
    if self.edge < self.max_edges:
      if not self.edge:
        # start a timer so it can time out and trigger decode/cleanup
        # timer period: how long until it expires and calls the callback function
        # TODO: calibrate the timer period better or find a better way to run the decode/cleanup
        self.tim.init(period = self.max_edges * 10, mode=Timer.ONE_SHOT, callback=self.cleanup)
      self.times[self.edge] = t
      self.edge += 1


  def decode(self, tim_obj):
    # decode is called by tim when it expires

    # take diffs of pulses and store them
    t = self.times  # short name for convenience 
    self.ir_periods = [ticks_diff(t[i+1], t[i]) for i in range(self.max_edges - 1)]

    # cleanup 
    # TODO: move cleanup to its own function?
    self.pin.irq(handler=None)
    tim_obj.deinit()

    # print results for convenience / feedback / testing
    print([round(i/1000) for i in self.ir_periods])
