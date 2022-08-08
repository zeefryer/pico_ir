from .rp2_rmt import RP2_RMT  # TODO: copy this from Peter Hinch's repo, check license etc

class IRTransmit():
  def __init__(self, pin, carrier_freq, pwm_duty):
    self.rmt = RP2_RMT(pin_pulse=None, carrier=(pin, carrier_freq, pwm_duty))

  def transmit(self, data):
    self.idx = 0 
    self.create_tx(data) 
    self.trigger() 

  def create_tx(self, data):
    # method must create self.pulse_times array (because it depends on data length)
    self.pulse_lengths = [0]
    raise NotImplementedError

  def trigger(self): 
    self.rmt.send(self.pulse_lengths)

  def append(self, *times): 
    # use this to add times to self.pulse_lengths so that the idx pointer is updated correctly
    for t in times:
      self.pulse_lengths[self.idx] = t
      self.idx += 1


class IRTransmitRoomba(IRTransmit):
  # remember to hardware-invert the signal since roomba is active low
  def __init__(self, pin):
    super().__init__(pin, carrier_freq=38000, pwm_duty=33)  # TODO: check these
    self.stop_pulse = 10000  # microseconds

  # TODO: split up create_tx to allow for sending multiple codes?

  def create_tx(self, data):
    data_bin = bin(data)[2:]  # TODO: doublecheck: reverse or not?
    tx_length = 2*len(data_bin) + 2
    self.pulse_lengths = [None for _ in range(tx_length)]
    for i in data_bin:
      if i == '1':
        self.append(3000, 1000)
      elif i == '0':
        self.append(1000, 3000)
    self.append(self.stop_pulse, 0)  # 0 tells the machine to switch off






