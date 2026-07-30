#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# Author: yutong
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import blocks
import math
from gnuradio import digital
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import zeromq
import sip
import threading



class audio_pluto_server(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "audio_pluto_server")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.variable_constellation = variable_constellation = digital.constellation_calcdist([-1-1j, -1+1j, 1+1j, 1-1j], [0, 1, 3, 2],
        4, 1, digital.constellation.AMPLITUDE_NORMALIZATION).base()
        self.variable_constellation.set_npwr(1.0)
        self.tx_gain_b = tx_gain_b = 20
        self.tx_gain = tx_gain = 0
        self.squelch_threshold = squelch_threshold = -50
        self.samp_rate = samp_rate = int(1e6)
        self.rx_gain_b = rx_gain_b = 20
        self.rx_gain = rx_gain = 0
        self.offset = offset = 200e3
        self.msg = msg = [1,2,3,4,5,6,7]
        self.freq_tx = freq_tx = 433720000
        self.freq_shift_1 = freq_shift_1 = 200000
        self.freq_shift = freq_shift = 200000
        self.freq_rx = freq_rx = 433720000
        self.audio_rate = audio_rate = int(48000)

        ##################################################
        # Blocks
        ##################################################

        self._freq_tx_range = qtgui.Range(432000000, 436000000, 1, 433720000, 200)
        self._freq_tx_win = qtgui.RangeWidget(self._freq_tx_range, self.set_freq_tx, "Transmitting Freq", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._freq_tx_win)
        self._freq_shift_range = qtgui.Range(-int(samp_rate/2), int(samp_rate/2), 1, 200000, 200)
        self._freq_shift_win = qtgui.RangeWidget(self._freq_shift_range, self.set_freq_shift, "'freq_shift'", "counter", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._freq_shift_win)
        self._freq_rx_range = qtgui.Range(432000000, 436000000, 1, 433720000, 200)
        self._freq_rx_win = qtgui.RangeWidget(self._freq_rx_range, self.set_freq_rx, "Receiving Freq", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._freq_rx_win)
        self.zeromq_push_sink_0 = zeromq.push_sink(gr.sizeof_float, 1, 'tcp://0.0.0.0:5555', 100, False, (-1), True)
        self._tx_gain_b_range = qtgui.Range(17, 73, 1, 20, 200)
        self._tx_gain_b_win = qtgui.RangeWidget(self._tx_gain_b_range, self.set_tx_gain_b, "Tx Gain Bladerf", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._tx_gain_b_win)
        self._tx_gain_range = qtgui.Range(0, 89.75, 0.25, 0, 200)
        self._tx_gain_win = qtgui.RangeWidget(self._tx_gain_range, self.set_tx_gain, "Tx Gain Pluto", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._tx_gain_win)
        self._rx_gain_b_range = qtgui.Range(-1, 60, 1, 20, 200)
        self._rx_gain_b_win = qtgui.RangeWidget(self._rx_gain_b_range, self.set_rx_gain_b, "Rx Gain Bladerf", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rx_gain_b_win)
        self._rx_gain_range = qtgui.Range(0, 71, 0.25, 0, 200)
        self._rx_gain_win = qtgui.RangeWidget(self._rx_gain_range, self.set_rx_gain, "Rx Gain Pluto", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._rx_gain_win)
        self.rational_resampler_xxx_1 = filter.rational_resampler_ccc(
                interpolation=12,
                decimation=25,
                taps=[],
                fractional_bw=0)
        self.rational_resampler_xxx_0 = filter.rational_resampler_ccc(
                interpolation=125,
                decimation=6,
                taps=[],
                fractional_bw=0)
        self.qtgui_sink_x_1 = qtgui.sink_c(
            1024, #fftsize
            window.WIN_BLACKMAN_hARRIS, #wintype
            freq_tx, #fc
            samp_rate, #bw
            "tx", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            True, #plotconst
            None # parent
        )
        self.qtgui_sink_x_1.set_update_time(1.0/5)
        self._qtgui_sink_x_1_win = sip.wrapinstance(self.qtgui_sink_x_1.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_1.enable_rf_freq(False)

        self.top_layout.addWidget(self._qtgui_sink_x_1_win)
        self.qtgui_sink_x_0_0_0_0 = qtgui.sink_c(
            1024, #fftsize
            window.WIN_BLACKMAN_hARRIS, #wintype
            freq_rx, #fc
            samp_rate, #bw
            "", #name
            True, #plotfreq
            True, #plotwaterfall
            True, #plottime
            True, #plotconst
            None # parent
        )
        self.qtgui_sink_x_0_0_0_0.set_update_time(1.0/5)
        self._qtgui_sink_x_0_0_0_0_win = sip.wrapinstance(self.qtgui_sink_x_0_0_0_0.qwidget(), Qt.QWidget)

        self.qtgui_sink_x_0_0_0_0.enable_rf_freq(False)

        self.top_layout.addWidget(self._qtgui_sink_x_0_0_0_0_win)
        self._offset_range = qtgui.Range(-samp_rate/2, samp_rate/2, samp_rate/100, 200e3, 200)
        self._offset_win = qtgui.RangeWidget(self._offset_range, self.set_offset, "Offset", "slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._offset_win)
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            10,
            firdes.low_pass(
                1,
                samp_rate,
                3e3,
                1e3,
                window.WIN_HAMMING,
                6.76))
        self._freq_shift_1_range = qtgui.Range(-int(samp_rate/2), int(samp_rate/2), 1, 200000, 200)
        self._freq_shift_1_win = qtgui.RangeWidget(self._freq_shift_1_range, self.set_freq_shift_1, "'freq_shift_1'", "counter", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._freq_shift_1_win)
        self.blocks_wavfile_source_0 = blocks.wavfile_source('guitar.mp3', True)
        self.blocks_freqshift_cc_0 = blocks.rotator_cc(2.0*math.pi*int(freq_shift)/samp_rate)
        self.analog_simple_squelch_cc_0 = analog.simple_squelch_cc(squelch_threshold, 1)
        self.analog_nbfm_tx_0 = analog.nbfm_tx(
        	audio_rate=audio_rate,
        	quad_rate=audio_rate,
        	tau=(75e-6),
        	max_dev=2500,
        	fh=(-1),
                )
        self.analog_nbfm_rx_0 = analog.nbfm_rx(
        	audio_rate=audio_rate,
        	quad_rate=audio_rate,
        	tau=(75e-6),
        	max_dev=2.5e3,
          )


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_nbfm_rx_0, 0), (self.zeromq_push_sink_0, 0))
        self.connect((self.analog_nbfm_tx_0, 0), (self.rational_resampler_xxx_0, 0))
        self.connect((self.analog_simple_squelch_cc_0, 0), (self.analog_nbfm_rx_0, 0))
        self.connect((self.analog_simple_squelch_cc_0, 0), (self.qtgui_sink_x_0_0_0_0, 0))
        self.connect((self.blocks_freqshift_cc_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.blocks_wavfile_source_0, 0), (self.analog_nbfm_tx_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.rational_resampler_xxx_1, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.blocks_freqshift_cc_0, 0))
        self.connect((self.rational_resampler_xxx_0, 0), (self.qtgui_sink_x_1, 0))
        self.connect((self.rational_resampler_xxx_1, 0), (self.analog_simple_squelch_cc_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "audio_pluto_server")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_variable_constellation(self):
        return self.variable_constellation

    def set_variable_constellation(self, variable_constellation):
        self.variable_constellation = variable_constellation

    def get_tx_gain_b(self):
        return self.tx_gain_b

    def set_tx_gain_b(self, tx_gain_b):
        self.tx_gain_b = tx_gain_b

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain

    def get_squelch_threshold(self):
        return self.squelch_threshold

    def set_squelch_threshold(self, squelch_threshold):
        self.squelch_threshold = squelch_threshold
        self.analog_simple_squelch_cc_0.set_threshold(self.squelch_threshold)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_freqshift_cc_0.set_phase_inc(2.0*math.pi*int(self.freq_shift)/self.samp_rate)
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, 3e3, 1e3, window.WIN_HAMMING, 6.76))
        self.qtgui_sink_x_0_0_0_0.set_frequency_range(self.freq_rx, self.samp_rate)
        self.qtgui_sink_x_1.set_frequency_range(self.freq_tx, self.samp_rate)

    def get_rx_gain_b(self):
        return self.rx_gain_b

    def set_rx_gain_b(self, rx_gain_b):
        self.rx_gain_b = rx_gain_b

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain

    def get_offset(self):
        return self.offset

    def set_offset(self, offset):
        self.offset = offset

    def get_msg(self):
        return self.msg

    def set_msg(self, msg):
        self.msg = msg

    def get_freq_tx(self):
        return self.freq_tx

    def set_freq_tx(self, freq_tx):
        self.freq_tx = freq_tx
        self.qtgui_sink_x_1.set_frequency_range(self.freq_tx, self.samp_rate)

    def get_freq_shift_1(self):
        return self.freq_shift_1

    def set_freq_shift_1(self, freq_shift_1):
        self.freq_shift_1 = freq_shift_1

    def get_freq_shift(self):
        return self.freq_shift

    def set_freq_shift(self, freq_shift):
        self.freq_shift = freq_shift
        self.blocks_freqshift_cc_0.set_phase_inc(2.0*math.pi*int(self.freq_shift)/self.samp_rate)

    def get_freq_rx(self):
        return self.freq_rx

    def set_freq_rx(self, freq_rx):
        self.freq_rx = freq_rx
        self.qtgui_sink_x_0_0_0_0.set_frequency_range(self.freq_rx, self.samp_rate)

    def get_audio_rate(self):
        return self.audio_rate

    def set_audio_rate(self, audio_rate):
        self.audio_rate = audio_rate




def main(top_block_cls=audio_pluto_server, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
