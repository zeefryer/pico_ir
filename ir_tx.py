from .rp2_rmt import RP2_RMT  # TODO: copy this from Peter Hinch's repo, check license etc
from array import array

class IRTransmit():
  def __init__(self, pin, carrier_freq, pwm_duty):
    self.rmt = RP2_RMT(pin_pulse=None, carrier=(pin, carrier_freq, pwm_duty))

  def transmit(self, data, reps=1):
    self.idx = 0 
    self.create_tx(data) 
    self.trigger(reps) 

  def create_tx(self, data):
    # override this in subclass to reflect individual IR protocol
    # method must create self.pulse_lengths array of pulse lengths in microseconds
    # note RP2_RMT expects array class, not generic iterable
    self.pulse_lengths = array('H', [0])  # 'H': unsigned short int
    raise NotImplementedError

  def trigger(self): 
    self.rmt.send(self.pulse_lengths, reps=reps, check=False)

  def append(self, *times): 
    # use this to add pulses to self.pulse_lengths so that the idx pointer is updated correctly
    for t in times:
      self.pulse_lengths[self.idx] = t
      self.idx += 1

  def add(self, t):
    # extend the most recent pulse in self.pulse_lengths by t microseconds
    self.pulse_lengths[self.idx-1] += t



class IRTransmitRoomba(IRTransmit):
  def __init__(self, pin, carrier_freq=None, pwm_duty=None):
    cf = carrier_freq or 38000  # need to doublecheck carrier freq and duty of roomba
    pd = pwm_duty or 33
    super().__init__(pin, carrier_freq=cf, pwm_duty=pd) 
    self.stop_pulse = 40000  # microseconds
    self.testing = False

  # TODO: split up create_tx to allow for sending multiple codes?

  def create_tx(self, data):
    data_bin = bin(data)[2:]  
    tx_length = 2*len(data_bin) + 1 + int(self.testing)*4
    self.pulse_lengths = array('H', 0 for _ in range(tx_length))
    if self.testing:
      self.append(1000, self.stop_pulse) 
    for i in data_bin:
      if i == '1':
        self.append(3000, 1000)
      elif i == '0':
        self.append(1000, 3000)
    self.add(self.stop_pulse)
    if self.testing:
      self.append(1000, 1000)
    self.append(0) 

  def trigger(self, reps): 
    self.rmt.send(self.pulse_lengths, reps=reps, check=True)







