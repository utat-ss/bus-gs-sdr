"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr


class blk(gr.sync_block):
    """Search for SYNC pattern and output aligned bits"""

    def __init__(self):
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='SYNC Finder',
            in_sig=[np.uint8],  # Input: unpacked bits
            out_sig=None  # No output
        )
        self.bit_buffer = []
        self.chars_saved = 0
        self.max_chars = 500
        self.sync_found = False
        self.sync_position = -1
        
        # SYNC pattern: 01010011 01011001 01001110 01000011
        self.sync_pattern = np.array([0,1,0,1,0,0,1,1,
                                       0,1,0,1,1,0,0,1,
                                       0,1,0,0,1,1,1,0,
                                       0,1,0,0,0,0,1,1], dtype=np.uint8)

    def find_sync(self, bits_array):
        """Search for SYNC pattern, return position"""
        sync_len = len(self.sync_pattern)
        for i in range(len(bits_array) - sync_len + 1):
            if np.array_equal(bits_array[i:i+sync_len], self.sync_pattern):
                return i
        return -1

    def work(self, input_items, output_items):
        """Find SYNC and save aligned data"""
        bits = input_items[0]
        
        if self.chars_saved >= self.max_chars:
            return len(bits)
        
        # Add bits to buffer
        for bit in bits:
            self.bit_buffer.append(int(bit))
        
        # Look for SYNC if not found yet
        if not self.sync_found and len(self.bit_buffer) >= len(self.sync_pattern):
            bits_array = np.array(self.bit_buffer, dtype=np.uint8)
            sync_pos = self.find_sync(bits_array)
            
            if sync_pos != -1:
                self.sync_found = True
                self.sync_position = sync_pos
                # Write initial marker
                with open("/home/tom/Documents/UofT/UTAT/SDR/Digital_Communication_System/data/rx_aligned_ascii.txt", "w") as f:
                    f.write(f"[SYNC FOUND AT BIT {sync_pos}]\n")
                with open("/home/tom/Documents/UofT/UTAT/SDR/Digital_Communication_System/data/rx_aligned_binary.txt", "w") as f:
                    f.write(f"[SYNC FOUND AT BIT {sync_pos}]\n")
        
        # Process bytes starting after SYNC
        if self.sync_found:
            # Start from after SYNC pattern
            start_idx = self.sync_position + len(self.sync_pattern)
            
            text_ascii = ""
            text_binary = ""
            
            i = start_idx
            while i + 8 <= len(self.bit_buffer) and self.chars_saved < self.max_chars:
                byte_bits = self.bit_buffer[i:i+8]
                
                # Convert to byte
                byte_val = 0
                for b in byte_bits:
                    byte_val = (byte_val << 1) | b
                
                text_ascii += chr(byte_val)
                text_binary += ''.join([str(int(b)) for b in byte_bits])
                
                self.chars_saved += 1
                i += 8
            
            # Write aligned files
            if text_ascii:
                with open("/home/tom/Documents/UofT/UTAT/SDR/Digital_Communication_System/data/rx_aligned_ascii.txt", "a") as f:
                    f.write(text_ascii)
            
            if text_binary:
                with open("/home/tom/Documents/UofT/UTAT/SDR/Digital_Communication_System/data/rx_aligned_binary.txt", "a") as f:
                    f.write(text_binary)
        
        return len(bits)