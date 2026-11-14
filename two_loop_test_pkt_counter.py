"""
Packet counter: counts every packet on SRS-4 Receiver csp_out.
Press "Reset count" to set the count back to 0.
"""
import threading
import pmt
from gnuradio import gr


class blk(gr.basic_block):
    def __init__(self, reset=0):
        gr.basic_block.__init__(self, name="Packet counter", in_sig=None, out_sig=None)
        self._reset = reset
        self._n = 0
        self._lock = threading.Lock()
        self.message_port_register_in(pmt.intern("in"))
        self.set_msg_handler(pmt.intern("in"), self._handle)

    # Called by GRC when the reset button changes; resets on the press
    @property
    def reset(self):
        return self._reset

    @reset.setter
    def reset(self, v):
        if v and not self._reset:
            with self._lock:
                self._n = 0
        self._reset = v

    def _handle(self, msg):
        with self._lock:
            self._n += 1

    def count(self):
        with self._lock:
            return self._n
