"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of all them are required to have default values!
"""

import numpy as np
from gnuradio import gr


class blk(gr.sync_block):
    """Output SYNC preamble once, then repeating message"""

    def __init__(self, message="HELLO"):
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Text Message Transmitter',
            in_sig=None,  # No input signal
            out_sig=[np.uint8]  # Output unpacked bits
        )
        
        # Preamble: SYNC (32 bits)
        self.preamble_bits = np.array([0,1,0,1,0,0,1,1,  # S
                                        0,1,0,1,1,0,0,1,  # Y
                                        0,1,0,0,1,1,1,0,  # N
                                        0,1,0,0,0,0,1,1], dtype=np.uint8)  # C
        
        # Message: convert string to bits
        self.message_bits = []
        for char in message:
            ascii_val = ord(char)
            for i in range(7, -1, -1):  # MSB first
                self.message_bits.append((ascii_val >> i) & 1)
        self.message_bits = np.array(self.message_bits, dtype=np.uint8)
        
        self.bit_index = 0
        self.chars_saved = 0
        self.max_chars = 100
        
        # Clear files on init
        from pathlib import Path

        DATA_DIR = Path.cwd() / "data"
        DATA_DIR.mkdir(exist_ok=True)

        (DATA_DIR / "tx_ascii.txt").write_text("")
        (DATA_DIR / "tx_binary.txt").write_text("")

    def work(self, input_items, output_items):
        """Output preamble once, then repeating message (save limited amount)"""
        
        output = output_items[0]
        n_bits = len(output)
        
        text_ascii = ""
        text_binary = ""
        
        for i in range(n_bits):
            if self.bit_index < len(self.preamble_bits):
                # Send preamble first
                output[i] = self.preamble_bits[self.bit_index]
                bit = self.preamble_bits[self.bit_index]
            else:
                # After preamble, loop the message
                message_offset = (self.bit_index - len(self.preamble_bits)) % len(self.message_bits)
                output[i] = self.message_bits[message_offset]
                bit = self.message_bits[message_offset]
            
            # Save to file if we haven't hit limit
            if self.chars_saved < self.max_chars * 8:  # 8 bits per char
                text_binary += str(int(bit))
                # Every 8 bits, add the ASCII char
                if len(text_binary) % 8 == 0:
                    byte_val = int(text_binary[-8:], 2)
                    text_ascii += chr(byte_val)
                    self.chars_saved += 1
            
            self.bit_index += 1

        # Write files (append mode)
        if text_ascii:
            with open(DATA_DIR / "tx_ascii.txt", "a") as f:
                f.write(text_ascii)

        if text_binary:
            with open(DATA_DIR / "tx_binary.txt", "a") as f:
                f.write(text_binary)

        return n_bits
