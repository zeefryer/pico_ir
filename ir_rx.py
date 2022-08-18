"""IR decoder for the Raspberry Pi Pico.

Author: Zee Fryer, 2022.
Based on the micropython_ir library by Peter Hinch.
"""

from machine import Timer, Pin
from utime import ticks_us, ticks_diff


class IRReceive():
  """Receive and decode IR pulses in a non-blocking manner.

  Args:
    pin: A machine.Pin instance corresponding to the IR receiver.
    verbose: Whether to print the pulse durations (default false).
  """
  def __init__(self, pin, verbose=False):
    self.pin = pin
    self.edge = 0
    self.tim = Timer(-1)
    self.verbose = verbose

  def start(self, num_edges=250):
    """Start the IR receiver in the background.

    Records the specified number of on/off pulses and automatically decodes and
    returns results.

    Args:
      num_edges: How many pulses to log.
    """
    print(
        f'IR Receiver: Recording IR pulses in the background, will time out in'
        '{num_edges/100:.3g} seconds.'
    )
    self.edge = 0  # reset counter to zero
    self.num_edges = num_edges

    self.times = [None for i in range(self.num_edges + 1)]

    # Start a timer that triggers decoding/cleanup on timeout.
    self.tim.init(
        period=self.num_edges * 10, mode=Timer.ONE_SHOT, callback=self.cleanup)

    # Calls _pin_cb every time the pin detects a rising or falling edge.
    self.pin.irq(handler=self._pin_cb, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)

  def _pin_cb(self, pin):
    """Callback/irq interrupt to allow for non-blocking recording of pulses.

    Args:
      pin: The pin instance that triggered the callback.
    """
    t = ticks_us()  # gets the timer value
    if self.edge <= self.num_edges:
      self.times[self.edge] = t
      self.edge += 1

  def _cleanup(self, calling_obj):
    """Called by timer when it expires.

    Args:
      calling_obj: The object that triggered the callback.
    """
    self.pin.irq(handler=None)
    calling_obj.deinit()

    # now decode the ticks as appropriate
    decoded = self._decode()
    print('IR Receiver: finished recording!')
    if self.verbose:
      self._pretty_print_decoded()
    return None

  def _decode(self):
    """Decode the collected pulse length data.

    Override this in subclasses to reflect specific IR protocols.

    Returns:
      List of pulse durations.
    """
    self.ir_periods = self.get_diffs()
    return self.ir_periods

  def _get_diffs(self):
    t = [x for x in self.times if x is not None] 
    return [ticks_diff(t[i+1], t[i]) for i in range(len(t)-1)]

  def _pretty_print_decoded(self):
    """Control what is printed when verbose=True.
    """
    print('Pulse duration in microseconds')
    for i, x in enumerate(self.ir_periods):
      print(f'{i}: {x}', end='\n')


class IRReceiveRoomba(IRReceive):
  """Receive and decode IR pulses from Roomba 500/600 series roombas, docks, etc

  Roomba uses a custom encoding: 3ms on/1ms off for 1, 1ms on/3ms off for 0.

  Args:
    pin: A machine.Pin instance corresponding to the IR receiver.
  """
  def __init__(self, pin, **kwargs):
    super().__init__(pin, **kwargs)
    self.decode_dict = {(1, 3): '0', (3, 1): '1'}
    self.min_divider_pulse = 4

  def _decode(self):
    ir_periods = self._get_diffs()
    bursts = self._separate_bursts(ir_periods)
    decoded = self._decode_bursts(bursts)
    self.ir_periods = ir_periods
    self.decoded = decoded
    return decoded

  def _pretty_print_decoded(self):
    print('Codes received:')
    print('\n'.join(str(i) for i in self.decoded))

  def _separate_bursts(self, ir_periods):
    """Process IR pulse lengths to prepare them for decoding.

    Groups pulse lengths into probable bursts by treating any pulse of length
    >= 4 milliseconds as a divider, correcting the final pulse length in each
    burst by dropping the divider pulse.

    Args:
      ir_periods: A list of pulse durations.
    """
    pulses = [round(x/1000) for x in ir_periods]  # values in milliseconds
    all_bursts = []
    first_burst = True
    current_burst = []
    for i, x in enumerate(pulses):
      if first_burst:
        # burst ends when we hit a value > min_divider_pulse
        first_burst = (x <= self.min_divider_pulse)  
      else:
        if x <= self.min_divider_pulse:
          current_burst.append(x)
        else:
          # Pulses appear in pairs (3, 1) or (1, 3) so we can record final pulse
          # and discard the noise from the dividing interval.
          current_burst.append(4-pulses[i-1]) 
          if len(current_burst) % 2 == 0:
            all_bursts.append([(current_burst[i], current_burst[i + 1])
                               for i in range(0, len(current_burst), 2)])
          current_burst = []
    return all_bursts 

  def _decode_bursts(self, bursts):
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
        result = int(decoded_str, 2)
      except ValueError:
        result = decoded_str
      all_results.append(result)
      current = []
    return all_results





