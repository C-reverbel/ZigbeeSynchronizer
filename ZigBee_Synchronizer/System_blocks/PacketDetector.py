from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.TimeSync import TimeSynchronizer
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
from System_blocks.SymbolDetector import SymbolDetector

import utils
import numpy as np
import matplotlib.pyplot as plt
from random import randint

class PacketDetector:
    def __init__(self, sampleRate, correlationSize, correlationDelay, secondCalculationDelay):
        self.sampleRate = sampleRate
        self.N = correlationSize
        self.T = correlationDelay
        self.D = secondCalculationDelay

        self.thresshold = 0.3

    def detectPacket(self, vector):
        len = vector.__len__()
        conj = np.conjugate(vector)
        C = []
        P = []
        M = []
        for i in range(len-self.T-self.N):
            c_temp = abs(sum(vector[i:i+self.N] * conj[i+self.T:i+self.T+self.N]))
            p_temp = abs(sum(conj[i+self.T:i+self.T+self.N]))
            C.append(c_temp)
            P.append(p_temp)
            M.append(c_temp/p_temp)
        return M


if __name__ == "__main__":
    DEBUG = 1
    err = []
    errCount = 0
    number_of_tests = 1
    for j in range(number_of_tests):
        # Zigbee packet
        sampleRate = 8
        if(DEBUG):
            zigbeePayloadNbOfBytes = 10
            freqOffset = 0.0
            phaseOffset = 0.
            SNR = 100.
        else:
            zigbeePayloadNbOfBytes = randint(5,127)
            freqOffset = float(randint(-200000,200000))
            phaseOffset = 0.0#float(randint(0,360))
            SNR = 8.
        leadingNoiseSamples = 70
        trailingNoiseSamples = 0

        if(DEBUG):
            print "Zigbee payload size = " + str(zigbeePayloadNbOfBytes) + " bytes"
            print "Sample rate = " + str(sampleRate) + " MHz"
            print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
            print "Phase offset = " + str(phaseOffset) + " Degrees"
            print "SNR = " + str(SNR) + " dB"
            print "\n"

        # payload in bytes, sample-rate in MHz
        myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
        N = myPacket.I.__len__()

        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate,  freqOffset, phaseOffset, SNR)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)

        # packet detector
        packetDetector = PacketDetector(sampleRate, 16, 8, 32)
        M = packetDetector.detectPacket(receivedSignal)

        lim = 200
        plt.plot(receivedSignal.real[:lim])
        plt.plot(M[:lim])
        plt.ylim([-2,10])
        plt.show()

    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests