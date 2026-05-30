import numpy as np
import pmt
from gnuradio import gr
from collections import deque


class blk(gr.sync_block):
    """
    Real-time BER align block.

    Inputs:
      in0: TX unpacked bits, uint8 values 0/1
      in1: RX unpacked bits, uint8 values 0/1

    Message output:
      ber_out: PMT pair (lag_bits, ber_float)

    Lag convention from np.correlate(rx, tx):
      lag > 0 means RX lags TX by lag bits
      lag < 0 means RX leads TX by -lag bits
    """

    def __init__(self, cal_size=4096, report_every=1024, window_size=100000):
        gr.sync_block.__init__(
            self,
            name="BER Align",
            in_sig=[np.uint8, np.uint8],
            out_sig=None,
        )

        self.CAL_SIZE = int(cal_size)
        self.REPORT_EVERY = int(report_every)
        self.WINDOW_SIZE = int(window_size)

        self._tx_cal = []
        self._rx_cal = []

        self._tx_q = deque()
        self._rx_q = deque()

        self._locked = False
        self._lag = 0
        self._did_initial_skip = False

        self._window_errors = deque()
        self._window_total = 0
        self._window_error_sum = 0

        self._since_report = 0

        self.message_port_register_out(pmt.intern("ber_out"))

    def _bits_for_corr(self, arr):
        arr = np.asarray(arr, dtype=np.uint8)

        # Important: this assumes values are already 0/1.
        # If values are 0/1/2/3 or raw bytes, this will warn.
        unique = np.unique(arr[:min(len(arr), 10000)])
        if not np.all((unique == 0) | (unique == 1)):
            print("[BER Align WARNING] Input contains values other than 0/1:", unique[:20])

        return (arr & 0x01).astype(np.float32) - 0.5

    def _find_lag(self):
        tx = self._bits_for_corr(self._tx_cal)
        rx = self._bits_for_corr(self._rx_cal)

        corr = np.correlate(rx, tx, mode="full")
        peak_idx = int(np.argmax(corr))
        lag = peak_idx - (len(tx) - 1)

        # np.correlate(rx, tx) convention:
        # positive lag means RX is delayed/lags TX.
        print(
            f"[BER Align] Calibration complete. Lag = {lag} bits "
            f"({'RX lags TX' if lag > 0 else 'RX leads TX' if lag < 0 else 'aligned'})"
        )

        return lag

    def _initial_skip_after_lock(self):
        """
        Since calibration samples were already consumed/discarded:
          lag > 0: RX lags TX, so future RX still contains old TX bits.
                   Skip lag RX bits.
          lag < 0: RX leads TX, so future TX is behind.
                   Skip -lag TX bits.
        """
        if self._did_initial_skip:
            return

        if self._lag > 0:
            skip = min(self._lag, len(self._rx_q))
            for _ in range(skip):
                self._rx_q.popleft()
        elif self._lag < 0:
            skip = min(-self._lag, len(self._tx_q))
            for _ in range(skip):
                self._tx_q.popleft()

        self._did_initial_skip = True

    def _add_to_window(self, errors, total):
        self._window_errors.append((errors, total))
        self._window_error_sum += errors
        self._window_total += total

        while self._window_total > self.WINDOW_SIZE and len(self._window_errors) > 0:
            old_errors, old_total = self._window_errors.popleft()
            self._window_error_sum -= old_errors
            self._window_total -= old_total

    def _emit_ber(self):
        ber = self._window_error_sum / self._window_total if self._window_total > 0 else 0.0

        msg = pmt.cons(
            pmt.from_long(int(self._lag)),
            pmt.from_double(float(ber)),
        )
        self.message_port_pub(pmt.intern("ber_out"), msg)

        print(
            f"[BER Align] window BER = {ber:.6f} "
            f"({self._window_error_sum}/{self._window_total}, lag={self._lag})"
        )

    def work(self, input_items, output_items):
        tx_in = np.asarray(input_items[0], dtype=np.uint8)
        rx_in = np.asarray(input_items[1], dtype=np.uint8)

        n = min(len(tx_in), len(rx_in))
        tx_in = tx_in[:n]
        rx_in = rx_in[:n]

        # Calibration phase
        if not self._locked:
            need = self.CAL_SIZE - len(self._tx_cal)
            take = min(need, n)

            self._tx_cal.extend(tx_in[:take].tolist())
            self._rx_cal.extend(rx_in[:take].tolist())

            if len(self._tx_cal) >= self.CAL_SIZE:
                self._lag = self._find_lag()
                self._locked = True

                # Any samples after the calibration part of this work call
                # should be used for BER, not thrown away.
                for b in tx_in[take:]:
                    self._tx_q.append(int(b & 0x01))
                for b in rx_in[take:]:
                    self._rx_q.append(int(b & 0x01))

            return n

        # Locked phase
        for b in tx_in:
            self._tx_q.append(int(b & 0x01))
        for b in rx_in:
            self._rx_q.append(int(b & 0x01))

        self._initial_skip_after_lock()

        cmp_len = min(len(self._tx_q), len(self._rx_q))

        if cmp_len > 0:
            tx_cmp = np.fromiter((self._tx_q.popleft() for _ in range(cmp_len)), dtype=np.uint8)
            rx_cmp = np.fromiter((self._rx_q.popleft() for _ in range(cmp_len)), dtype=np.uint8)

            errors = int(np.sum(tx_cmp != rx_cmp))
            self._add_to_window(errors, cmp_len)

            self._since_report += cmp_len

        if self._since_report >= self.REPORT_EVERY:
            self._emit_ber()
            self._since_report = 0

        return n
