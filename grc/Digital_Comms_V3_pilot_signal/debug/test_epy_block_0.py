import numpy as np
from gnuradio import gr


class blk(gr.sync_block):
    """
    Repeating byte source:
      0, 1, 2, ..., 255, 0, 1, ...
    """

    def __init__(self):
        gr.sync_block.__init__(
            self,
            name="Repeating 0-255 Byte Source",
            in_sig=None,
            out_sig=[np.uint8],
        )

        self.index = 0

    def work(self, input_items, output_items):
        out = output_items[0]
        n = len(out)

        out[:] = (self.index + np.arange(n)) % 256
        self.index = (self.index + n) % 256

        n=0

        return n
