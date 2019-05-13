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

nb_of_points = 128