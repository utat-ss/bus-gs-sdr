V3 is almost the same as V2, except that to compute the BER, we used a specific pilot signal. 

The pilot signal is a repeated stream of integers. Essentially: 

`0, 1, 2, 3, ..., 254, 255, 0, 1, 2, ..., 255, 0, ...`


# Still being debugged!

I need to double check my BER calculations though... Sometimes the locking clearly isn't working but the BER is still zero. 
