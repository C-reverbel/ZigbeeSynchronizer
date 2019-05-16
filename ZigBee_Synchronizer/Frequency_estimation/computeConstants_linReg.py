from System_blocks.ZigBeePacket import ZigBeePacket
import numpy as np
import matplotlib.pyplot as plt

# Zigbee packet
sampleRate = 8
zigbeePayloadNbOfBytes = 5

# ZIGBEE PACKET
# payload in bytes, sample-rate in MHz
myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
N = myPacket.I.__len__()


idealPhase = np.zeros(128)
idealPhase[::] = 1024 * np.unwrap(np.angle(myPacket.IQ[4:132]))

file = open("lut.txt", 'w')

for i in range(128):
    file.write("lut[" + str(i) + "] = " + str(int(idealPhase[i])) + ";" + "\n")

file.close()