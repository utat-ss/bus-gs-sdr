import numpy as np
from gnuradio import gr


class blk(gr.sync_block):
    """
    Continuous random byte source.

    Output:
      uint8 stream, values 0 to 255 inclusive.
    """

    def __init__(self, seed=0):
        gr.sync_block.__init__(
            self,
            name="Continuous Random Byte Source",
            in_sig=None,
            out_sig=[np.uint8],
        )

        # seed=0 means random/non-deterministic.
        # Any nonzero seed gives repeatable output across runs.
        if int(seed) == 0:
            self.rng = np.random.default_rng()
        else:
            self.rng = np.random.default_rng(int(seed))

    def work(self, input_items, output_items):
        out = output_items[0]
        n = len(out)

        out[:] = self.rng.integers(
            low=0,
            high=256,       # exclusive upper bound
            size=n,
            dtype=np.uint8,
        )

        return n
