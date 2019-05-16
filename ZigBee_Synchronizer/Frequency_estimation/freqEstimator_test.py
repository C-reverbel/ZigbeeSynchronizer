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
        ##self.kernel = [0., 0., 0., 0., np.pi/2, 0., 0., 0., 0., 0., 0., 0., -np.pi/2, 0., 0., 0., 0.]
        self.kernel = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1]

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
    freqOffset = -200000.0
    phaseOffset = 0.0
    SNR = 900.
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

    print "expected  = ", leadingNoiseSamples
    freqArray = [-200000.0, 0.0, 200000.0]
    for i in range(freqArray.__len__()):
        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate,  freqArray[i], phaseOffset, SNR)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)

        sts = TimeSynchronizer(sampleRate)
        estimate = sts.estimateDelay(receivedSignal)
        print estimate
        plt.plot(sts.correlation[:300])
        #plt.plot(sts.recPhase[:300])

        #plt.axvline(x=sts.index+sts.start, linewidth=0.5)

    #plt.xlabel("samples")
    #plt.ylabel("rad")
    #plt.title("Unwrapped Phase")
    #plt.legend(["-200 kHz", "0 kHz", "200 kHz"])
    #plt.axvline(x=4, color='k')
    #plt.axvline(x=132,color='k')
    #plt.axvline(x=132+128, color='k')
    #plt.show()

    plt.xlabel("samples")
    plt.title("Correlated Signal")
    plt.legend(["-200 kHz", "0 kHz", "200 kHz"])
    plt.show()



