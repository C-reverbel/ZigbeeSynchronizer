from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt
from random import randint

class SymbolDetector:
    def __init__(self, sampleRate):
        self.kernel = [1, 1, 1]
        self.sampleRate = sampleRate

    def detect(self, vector):
        N = (len(vector.real) - 4) / self.sampleRate
        self.corrI = np.correlate(vector.real, self.kernel, mode='full')
        self.corrQ = np.correlate(vector.imag, self.kernel, mode='full')

        self.satI = [1 if i > 0 else 0 for i in self.corrI]
        self.satQ = [1 if q > 0 else 0 for q in self.corrQ]
        # Symbol converter
        tempI = 0
        tempQ = 0
        outI = []
        outQ = []
        for i in range(self.satI.__len__() - 4):
            # I
            tempI += 1 if self.satI[i] > 0 else -1
            if i % 8 == 0:
                outI.append(1 if tempI > 0 else 0)
                tempI = 0
            # Q
            tempQ += 1 if self.satQ[i + 4] > 0 else -1
            if i % 8 == 0:
                outQ.append(1 if tempQ > 0 else 0)
                tempQ = 0
        # last point
        outI.append(1 if tempI > 0 else 0)
        outQ.append(1 if tempQ > 0 else 0)
        I_est = [-1 for i in range(N)]
        Q_est = [-1 for i in range(N)]
        for i in range(N):
            I_est[i] = 2*int(outI[1+i])-1
            Q_est[i] = 2*int(outQ[1+i])-1
        return I_est, Q_est

if __name__ == "__main__":
    DEBUG = 1
    errCount = 0
    number_of_tests = 1
    for j in range(number_of_tests):
        # Zigbee packet
        sampleRate = 8
        zigbeePayloadNbOfBytes = 127
        if(DEBUG):
            freqOffset = 0.0
            phaseOffset = 0.0
            SNR = 700.
        else:
            freqOffset = 0.0#float(randint(-200000,200000))
            phaseOffset = 0.0#float(randint(0,360))
            SNR = 6.
        leadingNoiseSamples = 0
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

        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate,  freqOffset, phaseOffset, SNR)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)

        # Ideal I and Q messages
        I = [2*int(i)-1 for i in myPacket.messageI]
        Q = [2*int(q)-1 for q in myPacket.messageQ]
        N = I.__len__()

        SD = SymbolDetector(8)
        I_est, Q_est = SD.detect(receivedSignal)

        errI = 0
        errQ = 0

        for i in range(N):
            if I[i] != I_est[i]:
                errI += 1
            if Q[i] != Q_est[i]:
                errQ += 1
        print "TEST ", j+1
        if errI or errQ:
            errCount += 1
            print "I = ", errI, "/", N, "error"
            print "Q = ", errQ, "/", N, "error"
            print "I  = ", I
            print "Ie = ", I_est, '\n'
            print "Q  = ",Q
            print "Qe = ", Q_est, '\n'


        if(DEBUG):
            plotMin = 0
            rang = 100
            plotMax = rang + plotMin
            plt.plot(SD.corrQ[plotMin:plotMax])
            plt.plot(SD.satQ[plotMin:plotMax],'x')
            plt.plot(receivedSignal.imag[plotMin:plotMax],'r')
            plt.plot(SD.kernel,'g')
            plt.axhline(y=0)
            plt.show()
        if(DEBUG):
            print I_est
            print I, '\n'
            print Q_est
            print Q, '\n'
    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests

