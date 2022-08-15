from .rp2_rmt import RP2_RMT 
from array import array


class IRTransmit():
  """
  Transmit IR pulses using Raspberry Pi Pico.
  """
  def __init__(self, pin, carrier_freq, pwm_duty):
    """
    Args:
      pin: A machine.Pin instance controlling the IR LED.
      carrier_freq: The frequency to transmit at (e.g. 38000).
      pwm_duty: PWM duty cycle, int 0-100.
    """
    self.rmt = RP2_RMT(pin_pulse=None, carrier=(pin, carrier_freq, pwm_duty))

  def transmit(self, data, reps=1):
    """
    Transmit a code on the specified pin.

    Args:
      data: Int, the value to be transmitted.
      reps: Number of times to repeat the transmission, default 1.
    """
    self.idx = 0 
    self._create_tx(data) 
    self._trigger(reps) 

  def _create_tx(self, data):
    """
    Prepare data for transmission.

    This should be overridden in subclasses to reflect individual IR protocols.
    Method must create self.pulse_lengths, an array of pulse lengths in 
    microseconds corresponding to LED on/off times.
    """
    self.pulse_lengths = array('H', [0])  # 'H': unsigned short int
    raise NotImplementedError

  def _trigger(self): 
    self.rmt.send(self.pulse_lengths, reps=reps, check=False)

  def _append(self, *times): 
    """
    Append values to pulse_lengths and automatically increment position counter.
    """
    for t in times:
      self.pulse_lengths[self.idx] = t
      self.idx += 1

  def _add(self, t):
    """
    Extend most recent pulse in array by specified duration (in microseconds).
    """
    self.pulse_lengths[self.idx-1] += t


class IRTransmitRoomba(IRTransmit):
  """
  Transmit IR codes to Roomba 500/600 series.

  Roomba uses a custom encoding: 3ms on/1ms off for 1, 1ms on/3ms off for 0. Gap
  between transmission bursts doesn't seem to matter, values recorded from dock
  vary from 4 to 90ms.
  """
  def __init__(self, pin, carrier_freq=None, pwm_duty=None):
    """
    Args:
      pin: A machine.Pin instance controlling the IR LED.
      carrier_freq: The frequency to transmit at (default 38000).
      pwm_duty: PWM duty cycle, int 0-100 (default 33).
    """
    cf = carrier_freq or 38000 
    pd = pwm_duty or 33
    super().__init__(pin, carrier_freq=cf, pwm_duty=pd) 

    # gap between transmission bursts
    self.stop_pulse = 40000 
    self.testing = False

  def _create_tx(self, data):
    data_bin = bin(data)[2:]  
    tx_length = 2*len(data_bin) + 1 + int(self.testing)*4
    self.pulse_lengths = array('H', 0 for _ in range(tx_length))

    # For testing with a separate IR receiver, helps to spread out bursts
    if self.testing:
      self._append(1000, self.stop_pulse) 

    for i in data_bin:
      if i == '1':
        self._append(3000, 1000)
      elif i == '0':
        self._append(1000, 3000)

    # Must add, not append here: don't want state to change.
    self._add(self.stop_pulse)
    if self.testing:
      self._append(1000, 1000)
    self._append(0)  # Tells RP2_RMT to end transmission.

  def _trigger(self, reps): 
    self.rmt.send(self.pulse_lengths, reps=reps, check=True)







