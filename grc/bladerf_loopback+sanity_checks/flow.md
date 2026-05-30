**Tx**

1. Random Source
- goes from 0 to 255
- 1 byte

2. Unpack K bits, k=8
- 1 byte to 8 bits
- file size = 16M (ber_input.txt)

3. Pack k bits, k = 2
- 2 bits to 1 complex_bit
- 4 "complex_bits"(0, 1, 2, 3)
- file size = 7.8M (ber_input1.txt)

4. Constellation Modulator
- Constellation is regular QPSK
- Yes differential encoding
- Complex_bits to complex signal (blue)
- sps = 8
- file size = 2.0G (ber_input_c.txt) (consider that complex signals are probably not stored in a unicode char? Idk)

5. RRC Filter

6. Virtual Sink

**Rx**

1. Virtual Source
- output is ber_output_c1.txt, size = 2.0G

2. Symbol Sync
- "Divide by sps"
- ber_output_c2.txt, size = 246M

3. Costas Loop
- Phase correction
- output is ber_input_c3.txt, size = 246M

4. Constellation Decoder
- complex to 0123 ("complex_bits") (right??????) (Am I tripping up here? )
- same constellation object
- ber_output1.txt, size = 31M

5. Unpack 2 bits
- 0123 to 01 ("complex_bits" to bits)
- ber_output.txt, size = 62M
