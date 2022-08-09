from machine import Timer, Pin
from utime import ticks_us, ticks_diff


class IRReceive():
  def __init__(self, pin, verbose=False):
    self.pin = pin
    self.edge = 0
    self.tim = Timer(-1)
    self.verbose = verbose
    self.value = pin.value()

  def pin_cb(self, pin):
    # pin callback expects exactly one argument, namely the pin
    t = ticks_us()  # gets the timer value
    v = pin.value()  # get the pin value so we can evaluate if it's rising or falling
    if self.edge <= self.num_edges:
      if v < self.value:
        self.times[self.edge] = ('l', t)  # now low
      elif v > self.value:
        self.times[self.edge] = ('h', t)  # now high
      else:
        self.times[self.edge] = ('u', t)  # unknown; for testing
      self.value = v 
      self.edge += 1

  def start(self, num_edges=250):
    print(f'IR Receiver: Recording IR pulses in the background for the next {num_edges/100:.3g} seconds.\nStarting...')
    self.edge = 0  # reset to zero
    self.num_edges = num_edges
    # create the array ahead of time for speed
    self.times = [None for i in range(self.num_edges+1)]
    # start a timer so it can time out and trigger decode/cleanup
    # timer period: how long until it expires and calls the callback function
    # TODO: calibrate the timer period better or find a better way to run the decode/cleanup
    self.tim.init(period = self.num_edges * 10, mode=Timer.ONE_SHOT, callback=self.cleanup)
    # now set up the interrupt on the pin, which calls the handler fn when triggered
    self.pin.irq(handler=self.pin_cb, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)  

  def cleanup(self, tim_obj):
    # called by tim when it expires
    # expects exactly one arg namely the timer
    # first clean up the logging objects
    self.pin.irq(handler=None)
    tim_obj.deinit()

    # now decode the ticks as appropriate
    decoded = self.decode()
    print('IR Receiver: finished recording!')
    if self.verbose:
      self.pretty_print_decoded()
    return None

  def decode(self):
    self.ir_periods = self.get_diffs()
    return self.ir_periods

  def get_diffs(self):
    t = [x for x in self.times if x is not None] 
    return [(t[i][0], ticks_diff(t[i+1][1], t[i][1])) for i in range(len(t)-1)]

  def pretty_print_decoded(self):
    print('Pulse type (high or low) and duration in microseconds')
    for x in self.ir_periods:
      print(f'{x[0]}: {x[1]}', end='\n')


class IRReceiveRoomba(IRReceive):
  def __init__(self, pin, **kwargs):
    super().__init__(pin, **kwargs)
    self.decode_dict = {(1,3): '0', (3,1): '1'}

  def decode(self):
    ir_periods = self.get_diffs()
    bursts = self.separate_bursts(ir_periods)
    decoded = self.decode_bursts(bursts)
    self.ir_periods = ir_periods
    self.decoded = decoded
    return decoded

  def pretty_print_decoded(self):
    print('Codes received:')
    print('\n'.join(str(i) for i in self.decoded))

  def separate_bursts(self, ir_periods):
    pulses = [round(x[1]/1000) for x in ir_periods]  # extract the values in milliseconds
    all_bursts = []
    first_burst = True
    current_burst = []
    for i, x in enumerate(pulses):
      if first_burst:
        first_burst = (x <= 4) # burst ends when we hit a value >= 5
      else:
        if x <= 4:
          current_burst.append(x)
        else:
          # we've reached the end of a burst
          # it appears the interval length between bursts doesn't matter
          current_burst.append(4-pulses[i-1])  # can't be out of range because first_burst always true at i=0
          if len(current_burst) % 2 == 0:
            all_bursts.append([(current_burst[i], current_burst[i+1]) for i in range(0, len(current_burst), 2)])
          current_burst = []
    return all_bursts 

  def decode_bursts(self, bursts):
    all_results = []
    current = []
    for x in bursts:
      for bitpair in x:
        try:
          current.append(self.decode_dict[bitpair])
        except (KeyError, IndexError):
          current.append('x')
      decoded_str = ''.join(current)
      try:
        result = int(decoded_str,2)
      except:
        result = decoded_str
      all_results.append(result)
      current = []
    return all_results





