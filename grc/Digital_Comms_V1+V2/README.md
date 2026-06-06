V1 is a digital communication system simulation, made by the goated Tom Haene.
 
V2 has the same structure, but it is tested with hardware: 
* real time BER calculator (a little bit buggy at times)
* Random Byte Source used. 
* BER calculated by periodically aligning & comparing the src signal (Tx)  and decoded signal (Rx). 



# Explainations on Main Blocks

This are the main parts of the flowgraph, updated from flow.md:


### Tx

1. Random Source
    - goes from 0 to 255
    - 1 byte


2. Constellation Modulator
* Unpacks the 1 byte (0-255) to 8 bits (0or1)
* Turns the 8 bits to 4 "complex bits" (Through the QPSK constellation, which turns 0123 to 1+j, 1-j, etc etc)
* Differential encoding

Notes:

    - Constellation is regular QPSK
    - Yes differential encoding
    - Complex_bits to complex signal (blue)
    - sps = 8
    - This block does a lot... beware

4. RRC Filter
    - Pulse shaping

5. Virtual Sink (to be replaced by SDR sink)


### Rx

1. Virtual Source (to be replaced by SDR source)

1. (Optional on hardware??) Low pass filter

2. Symbol Sync
    - "Divide by sps"
    - chooses best sample (sampling)

3. Costas Loop
    - Phase correction (to "stop the constellation from rotating")

4. Constellation Decoder
    - complex to 0123 ("complex_bits")
    - same constellation object

5. Unpack 2 bits
    - 0123 to 01 ("complex_bits" to bits)

