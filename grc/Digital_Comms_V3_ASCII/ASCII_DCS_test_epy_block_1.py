"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr


class blk(gr.sync_block):
    """Convert unpacked bits to packed bytes, save binary and ASCII versions"""

    def __init__(self):
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='Bits to ASCII',
            in_sig=[np.uint8],  # Input: unpacked bits
            out_sig=None  # No output
        )
        self.bit_buffer = []
        self.chars_saved = 0
        self.max_chars = 100

    def work(self, input_items, output_items):
        """Pack bits into bytes and save binary and ASCII versions"""
        bits = input_items[0]
        
        # Stop saving if we've hit the limit
        if self.chars_saved >= self.max_chars:
            return len(bits)
        
        # Add bits to buffer
        for bit in bits:
            self.bit_buffer.append(int(bit))
        
        # Process complete bytes (8 bits at a time)
        text_ascii = ""
        text_binary = ""
        while len(self.bit_buffer) >= 8 and self.chars_saved < self.max_chars:
            byte_bits = self.bit_buffer[:8]
            self.bit_buffer = self.bit_buffer[8:]
            
            # Convert 8 bits to a byte value
            byte_val = 0
            for i, b in enumerate(byte_bits):
                byte_val = (byte_val << 1) | b
            
            # ASCII conversion
            text_ascii += chr(byte_val)
            
            # Binary conversion (8 bits as '01010101')
            text_binary += ''.join([str(int(b)) for b in byte_bits])
            
            self.chars_saved += 1
        
        # Write both files
        if text_ascii:
            with open("/home/tom/Documents/UofT/UTAT/SDR/Digital_Communication_System/data/tx_ascii.txt", "a") as f:
                f.write(text_ascii)
        
        if text_binary:
            with open("/home/tom/Documents/UofT/UTAT/SDR/Digital_Communication_System/data/tx_binary.txt", "a") as f:
                f.write(text_binary)
        
        return len(bits)