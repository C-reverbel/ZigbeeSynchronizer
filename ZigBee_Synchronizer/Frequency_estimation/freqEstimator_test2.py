from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt
from random import randint

class TimeSynchronizer:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        packet = ZigBeePacket(0, self.sampleRate)
        #self.kernel = np.unwrap(np.angle(packet.IQ[10:18]))#tot = 5
        #self.kernel = np.unwrap(np.angle(packet.IQ[124:140]))#tot = 32
        #self.kernel = np.unwrap(np.angle(packet.IQ[116:133]))  # tot = 32
        #self.kernel = [0., 0., 0., 0., np.pi/2, 0., 0., 0., 0., 0., 0., 0., -np.pi/2, 0., 0., 0., 0.]
        self.kernel = [np.pi / 2, 0., 0., 0., 0., 0., 0., 0., -np.pi / 2]

    def estimateDelay(self, vector):
        self.recPhase = np.unwrap(np.angle(vector))
        self.correlation = np.correlate(self.recPhase, self.kernel, mode='full')
        #start = 150
        self.start = 102#142
        self.range = 28#35
        #range = 100
        self.index = np.argmax(self.correlation[self.start:self.start + self.range])

        return self.index + self.start - 162 + 58#- 144
        #return index + start - 167 # 150 - 200


if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 0
    freqOffset = 200000.0
    phaseOffset = 0.0
    SNR = 7.
    leadingNoiseSamples = 0
    trailingNoiseSamples = 0

    print "Zigbee payload size = " + str(zigbeePayloadNbOfBytes) + " bytes"
    print "Sample rate = " + str(sampleRate) + " MHz"
    print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
    print "Phase offset = " + str(phaseOffset) + " Degrees"
    print "SNR = " + str(SNR) + " dB"
    print "\n"

    # payload in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
    N = myPacket.I.__len__()

    freqArray = [0.0]
    count = 0
    tol = 2
    for i in range(200):
        leadingNoiseSamples = randint(0,28)
        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate,  freqOffset, phaseOffset, SNR)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)

        #plt.subplot(2, 1, 1)
        #plt.plot(np.unwrap(np.angle(myPacket.IQ[7:156])))
        #plt.subplot(2,1,2)
        #plt.plot(np.unwrap(np.angle(myPacket.IQ[35:184])))
        #plt.show()

        sts1 = TimeSynchronizer(sampleRate)
        estimate1 = sts1.estimateDelay(receivedSignal[7:156])

        sts2 = TimeSynchronizer(sampleRate)
        estimate2 = sts2.estimateDelay(receivedSignal[35:184])

        low = 63
        high = 100
        corrRange = 149

        max = 0
        maxIndex = 0
        for i in range(high - low):
            temp = sts2.correlation[low + i]
            if (temp > max and maxIndex + 25 > i):
                max = temp
                maxIndex = i
        index = maxIndex + low
        finalIndex = index - 65
        print "expected  = ", leadingNoiseSamples, "got  = ", finalIndex

        if(finalIndex > leadingNoiseSamples+tol or finalIndex < leadingNoiseSamples-tol):
            pass
        else:
            count = count + 1

        #plt.subplot(2, 1, 1)
        #plt.plot(sts1.correlation[:corrRange],'-x')
        #plt.axvline(x=low, color='k')
        #plt.axvline(x=high, color='k')
        #plt.subplot(2, 1, 2)
        #plt.plot(sts2.correlation[:corrRange],'-x')
        #plt.axvline(x=low, color='k')
        #plt.axvline(x=high, color='k')
        #plt.axvline(x=index2, color='r')
    #plt.show()
    print count


    plt.plot(sts2.correlation[:corrRange],'-x')
    plt.axvline(x=low, color='k')
    plt.axvline(x=high, color='k')
    plt.axvline(x=index, color='r')
    plt.show()