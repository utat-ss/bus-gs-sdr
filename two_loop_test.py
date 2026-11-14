#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import analog
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import network
from gnuradio import satlab
import sip
import threading
import time
import two_loop_test_pkt_counter as pkt_counter  # embedded python block



class two_loop_test(gr.top_block, Qt.QWidget):

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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "two_loop_test")

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
        self.pkt_sent = pkt_sent = 2000
        self.pkt_count = pkt_count = 0
        self.symbol_rate = symbol_rate = 1000000
        self.samp_rate = samp_rate = 4e6
        self.rs = rs = True
        self.pkt_reset = pkt_reset = 0
        self.pkt_count_lbl = pkt_count_lbl = pkt_count
        self.per_lbl = per_lbl = "{:.2f} %  ({} lost)".format(100.0*(1 - pkt_count/pkt_sent), pkt_sent - pkt_count) if pkt_sent > 0 else "set N"
        self.noise_amp = noise_amp = 0
        self.crc = crc = True
        self.cc = cc = True

        ##################################################
        # Blocks
        ##################################################

        _pkt_reset_push_button = Qt.QPushButton('Reset count')
        _pkt_reset_push_button = Qt.QPushButton('Reset count')
        self._pkt_reset_choices = {'Pressed': 1, 'Released': 0}
        _pkt_reset_push_button.pressed.connect(lambda: self.set_pkt_reset(self._pkt_reset_choices['Pressed']))
        _pkt_reset_push_button.released.connect(lambda: self.set_pkt_reset(self._pkt_reset_choices['Released']))
        self.top_grid_layout.addWidget(_pkt_reset_push_button, 12, 0, 1, 1)
        for r in range(12, 13):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.satlab_srs4_tx_0 = satlab.srs4_tx(
            samp_rate=20e6,
            rate=symbol_rate,
            size=217,
            idnum=0,
            cc=cc,
            rs=rs,
            crc=crc,
            rand=True,
            key="\x00" * 32,
            encrypt=False,
            auth=False,
            rolloff=0.2,
            constellation='QPSK',
            idleframes=10000,
            max_in_flight=100,
        )
        self.satlab_srs4_rx_0 = satlab.srs4_rx(
            samp_rate=20e6,
            rate=symbol_rate,
            size=217,
            idnum=0,
            cc=cc,
            rs=rs,
            crc=crc,
            rand=True,
            key="\x00" * 32,
            auth=False,
            decrypt=False,
            rolloff=0.2,
            constellation='QPSK',
        )
        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            1024, #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(False)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_0_win)
        self._pkt_sent_tool_bar = Qt.QToolBar(self)
        self._pkt_sent_tool_bar.addWidget(Qt.QLabel("Packets sent (N)" + ": "))
        self._pkt_sent_line_edit = Qt.QLineEdit(str(self.pkt_sent))
        self._pkt_sent_tool_bar.addWidget(self._pkt_sent_line_edit)
        self._pkt_sent_line_edit.editingFinished.connect(
            lambda: self.set_pkt_sent(int(str(self._pkt_sent_line_edit.text()))))
        self.top_grid_layout.addWidget(self._pkt_sent_tool_bar, 13, 0, 1, 1)
        for r in range(13, 14):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.pkt_counter = pkt_counter.blk(reset=pkt_reset)
        self._pkt_count_lbl_tool_bar = Qt.QToolBar(self)

        if None:
            self._pkt_count_lbl_formatter = None
        else:
            self._pkt_count_lbl_formatter = lambda x: str(x)

        self._pkt_count_lbl_tool_bar.addWidget(Qt.QLabel("Packets received"))
        self._pkt_count_lbl_label = Qt.QLabel(str(self._pkt_count_lbl_formatter(self.pkt_count_lbl)))
        self._pkt_count_lbl_tool_bar.addWidget(self._pkt_count_lbl_label)
        self.top_grid_layout.addWidget(self._pkt_count_lbl_tool_bar, 12, 1, 1, 1)
        for r in range(12, 13):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        def _pkt_count_probe():
          self.flowgraph_started.wait()
          while True:

            val = self.pkt_counter.count()
            try:
              try:
                self.doc.add_next_tick_callback(functools.partial(self.set_pkt_count,val))
              except AttributeError:
                self.set_pkt_count(val)
            except AttributeError:
              pass
            time.sleep(1.0 / (10))
        _pkt_count_thread = threading.Thread(target=_pkt_count_probe)
        _pkt_count_thread.daemon = True
        _pkt_count_thread.start()
        self._per_lbl_tool_bar = Qt.QToolBar(self)

        if None:
            self._per_lbl_formatter = None
        else:
            self._per_lbl_formatter = lambda x: str(x)

        self._per_lbl_tool_bar.addWidget(Qt.QLabel("PER"))
        self._per_lbl_label = Qt.QLabel(str(self._per_lbl_formatter(self.per_lbl)))
        self._per_lbl_tool_bar.addWidget(self._per_lbl_label)
        self.top_grid_layout.addWidget(self._per_lbl_tool_bar, 13, 1, 1, 1)
        for r in range(13, 14):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.network_socket_pdu_0 = network.socket_pdu('UDP_SERVER', '', '52003', 10000, False)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_noise_source_x_0 = analog.noise_source_c(analog.GR_GAUSSIAN, noise_amp, 0)


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.network_socket_pdu_0, 'pdus'), (self.satlab_srs4_tx_0, 'csp_in'))
        self.msg_connect((self.satlab_srs4_rx_0, 'csp_out'), (self.pkt_counter, 'in'))
        self.connect((self.analog_noise_source_x_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_add_xx_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.satlab_srs4_rx_0, 0))
        self.connect((self.satlab_srs4_rx_0, 0), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.satlab_srs4_tx_0, 0), (self.blocks_add_xx_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "two_loop_test")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_pkt_sent(self):
        return self.pkt_sent

    def set_pkt_sent(self, pkt_sent):
        self.pkt_sent = pkt_sent
        self.set_per_lbl("{:.2f} %  ({} lost)".format(100.0*(1 - self.pkt_count/self.pkt_sent), self.pkt_sent - self.pkt_count) if self.pkt_sent > 0 else "set N")
        Qt.QMetaObject.invokeMethod(self._pkt_sent_line_edit, "setText", Qt.Q_ARG("QString", str(self.pkt_sent)))

    def get_pkt_count(self):
        return self.pkt_count

    def set_pkt_count(self, pkt_count):
        self.pkt_count = pkt_count
        self.set_per_lbl("{:.2f} %  ({} lost)".format(100.0*(1 - self.pkt_count/self.pkt_sent), self.pkt_sent - self.pkt_count) if self.pkt_sent > 0 else "set N")
        self.set_pkt_count_lbl(self.pkt_count)

    def get_symbol_rate(self):
        return self.symbol_rate

    def set_symbol_rate(self, symbol_rate):
        self.symbol_rate = symbol_rate
        self.satlab_srs4_rx_0.set_rate(self.symbol_rate)
        self.satlab_srs4_tx_0.set_rate(self.symbol_rate)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)

    def get_rs(self):
        return self.rs

    def set_rs(self, rs):
        self.rs = rs
        self.satlab_srs4_rx_0.set_rs(self.rs)
        self.satlab_srs4_tx_0.set_rs(self.rs)

    def get_pkt_reset(self):
        return self.pkt_reset

    def set_pkt_reset(self, pkt_reset):
        self.pkt_reset = pkt_reset
        self.pkt_counter.reset = self.pkt_reset

    def get_pkt_count_lbl(self):
        return self.pkt_count_lbl

    def set_pkt_count_lbl(self, pkt_count_lbl):
        self.pkt_count_lbl = pkt_count_lbl
        Qt.QMetaObject.invokeMethod(self._pkt_count_lbl_label, "setText", Qt.Q_ARG("QString", str(self._pkt_count_lbl_formatter(self.pkt_count_lbl))))

    def get_per_lbl(self):
        return self.per_lbl

    def set_per_lbl(self, per_lbl):
        self.per_lbl = per_lbl
        Qt.QMetaObject.invokeMethod(self._per_lbl_label, "setText", Qt.Q_ARG("QString", str(self._per_lbl_formatter(self.per_lbl))))

    def get_noise_amp(self):
        return self.noise_amp

    def set_noise_amp(self, noise_amp):
        self.noise_amp = noise_amp
        self.analog_noise_source_x_0.set_amplitude(self.noise_amp)

    def get_crc(self):
        return self.crc

    def set_crc(self, crc):
        self.crc = crc
        self.satlab_srs4_rx_0.set_crc(self.crc)
        self.satlab_srs4_tx_0.set_crc(self.crc)

    def get_cc(self):
        return self.cc

    def set_cc(self, cc):
        self.cc = cc
        self.satlab_srs4_rx_0.set_cc(self.cc)
        self.satlab_srs4_tx_0.set_cc(self.cc)




def main(top_block_cls=two_loop_test, options=None):

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
