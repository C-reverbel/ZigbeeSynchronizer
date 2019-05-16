from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt
from random import randint


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
            SNR = 8.
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
        I = [int(i) for i in myPacket.messageI]
        Q = [int(q) for q in myPacket.messageQ]

        # correlate and saturate signals
        kernel = [1, 1]
        corrI = np.correlate(receivedSignal.real, kernel, mode='full')
        corrQ = np.correlate(receivedSignal.imag, kernel, mode='full')

        satI = [1 if i > 0 else 0 for i in corrI]
        satQ = [1 if q > 0 else 0 for q in corrQ]
        # Symbol converter
        tempI = 0
        tempQ = 0
        outI = []
        outQ = []
        for i in range(satI.__len__() - 4):
            # I
            tempI += 1 if satI[i] > 0 else -1
            if i % 8 == 0:
                outI.append(1 if tempI > 0 else 0)
                tempI = 0
            # Q
            tempQ += 1 if satQ[i+4] > 0 else -1
            if i % 8 == 0:
                outQ.append(1 if tempQ > 0 else 0)
                tempQ = 0
        # last point
        outI.append(1 if tempI > 0 else 0)
        outQ.append(1 if tempQ > 0 else 0)
        I_est = outI[1:-1]
        Q_est = outQ[1:-1]

        errI = 0
        errQ = 0
        N = I.__len__()
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
            plt.plot(corrQ[plotMin:plotMax])
            plt.plot(satQ[plotMin:plotMax],'x')
            plt.plot(receivedSignal.imag[plotMin:plotMax],'r')
            plt.plot(kernel,'g')
            plt.axhline(y=0)
            plt.show()
        if(DEBUG):
            print I_est
            print I, '\n'
            print Q_est
            print Q, '\n'
    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests