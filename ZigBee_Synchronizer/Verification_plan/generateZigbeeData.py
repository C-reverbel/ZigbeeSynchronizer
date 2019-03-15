#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
import sys
sys.path.append('../')

from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
import utils
import numpy as np
import matplotlib.pyplot as plt

def twos_comp(val):
    res = int(val)
    if res < 0:
        res = int("{0:016b}".format(res))
        print "res = ", res
        res = ~res
    return res

if __name__ == "__main__":
    # Zigbee packet
    nbOfSamples = 128
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 0.e3
    phaseOffset = 0.
    SNR = 100.

    # Butterworth low-pass filter
    cutoff = 2.5e6
    fs = sampleRate * 1e6
    order = 0

    # payload in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
    N = myPacket.I.__len__()

    # time vector
    maxTime = (1e-6 / sampleRate) * N
    timeStep = 1e-6 / sampleRate
    time = np.arange(0, maxTime, timeStep)

    # channel
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    receivedSignal = utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order)

    # Reduce number of bits
    nbOfBits = 16
    InPhase = np.zeros(N)
    Quadrature = np.zeros(N)
    maxVal = (2 ** (nbOfBits - 1) - 1)
    for i in range(N):
        tempR = int(receivedSignal.real[i] * maxVal)
        tempI = int(receivedSignal.imag[i] * maxVal)

        InPhase[i] = maxVal if tempR > maxVal else (-maxVal if tempR < -maxVal else tempR)
        Quadrature[i] = maxVal if tempI > maxVal else (-maxVal if tempI < -maxVal else tempI)

        InPhase[i] = int(InPhase[i])
        Quadrature[i] = int(Quadrature[i])


    plt.plot(InPhase[:50],'b')
    plt.plot(Quadrature[:50], 'r')
    plt.axhline(linewidth=2, color='g', y=maxVal)
    plt.axhline(linewidth=2, color='g', y=-maxVal)
    plt.show()

    for i in range(16):
        #print format(int(InPhase[i]), '017b')
        print twos_comp(InPhase[i])
