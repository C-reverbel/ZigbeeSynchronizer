from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel

import numpy as np
import matplotlib.pyplot as plt
from random import randint


class PacketDetector:
    def __init__(self, sampleRate, correlationSize = 16, correlationDelay = 8, secondCalculationDelay = 16):
        self.sampleRate = sampleRate
        self.N = correlationSize
        self.T = correlationDelay
        self.D = secondCalculationDelay

        self.threshold = 0.45
        self.secondObservationTime = 32

    def detectPacket(self, vector):
        C, P, M = self._computeCPM(vector)
        return self._computeStartIndex(M)

    def _computeStartIndex(self,M):
        done = 0
        index = 0
        len = M.__len__()
        while not done:
            if index > len:
                done = 1
                print "OUT OF RANGE",
            temp = self._indexFirstElementBiggerThan(M[index:], self.threshold)
            if temp:
                index += temp
            in2_start = index + self.D
            in2_end   = in2_start + self.secondObservationTime
            index2 = self._indexFirstElementBiggerThan(M[in2_start:in2_end], self.threshold)
            if index2 != -1:
                index += index2
                done = 1
            else:
                index += self.D
        return index
    def _indexFirstElementBiggerThan(self,vector,threshold):
        try:
            return next(x[0] for x in enumerate(vector) if x[1] > threshold)
        except:
            return -1
    def _computeCPM(self,vector):
        len = vector.__len__()
        conj = np.conjugate(vector)
        C = []
        P = []
        M = []
        for i in range(len - self.T - self.N):
            c_temp = abs(sum(vector[i:i + self.N] * conj[i + self.T:i + self.T + self.N]))
            p_temp = sum(np.sqrt(abs(conj[i:i + self.N]) ** 2))
            C.append(c_temp)
            P.append(p_temp)
            M.append(c_temp / p_temp)
        C = np.append(np.zeros(self.N + self.T), C)
        P = np.append(np.zeros(self.N + self.T), P)
        M = np.append(np.zeros(self.N + self.T), M)
        return C, P, M

if __name__ == "__main__":
    DEBUG = 1
    errCount = 0
    number_of_tests = 1
    delta =[]
    for j in range(number_of_tests):
        err = 0
        # Zigbee packet
        sampleRate = 8
        pd_correlationSize = 16
        pd_delay = 8
        pd_delaySecondComputation = 16
        if(DEBUG):
            zigbeePayloadNbOfBytes = 5
            freqOffset = 0.0
            phaseOffset = 0.0
            SNR = 10.
        else:
            zigbeePayloadNbOfBytes = 1
            freqOffset = float(randint(-200000,200000))
            phaseOffset = float(randint(0,360))
            SNR = 5.
        leadingNoiseSamples = randint(1,20) * 50
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
        receivedSignal = .8 * myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)

        # packet detector
        packetDetector = PacketDetector(sampleRate, pd_correlationSize, pd_delay, pd_delaySecondComputation)
        C, P, M = packetDetector._computeCPM(receivedSignal)
        index = packetDetector.detectPacket(receivedSignal)

        delta.append(index - leadingNoiseSamples)

        print "TEST", j+1, "START OF PACKET", leadingNoiseSamples, "ESTIMATED VALUE", index, "DELTA", delta[-1],
        if(index >= leadingNoiseSamples and index < leadingNoiseSamples + 1024):
            print " OK"
        else:
            print " ERROR"
            errCount += 1
            err = 1
        if(err or DEBUG):
            lim = leadingNoiseSamples + 100
            plt.axvline(x=index, linewidth=4, color='k')
            plt.plot(receivedSignal.real[:lim], linewidth=0.5)
            plt.plot(receivedSignal.imag[:lim], linewidth=0.5)
            #plt.plot(C[:lim], 'g')
            #plt.plot(P[:lim], 'b')
            plt.plot(M[:lim], 'r', linewidth=2)
            plt.axhline(y=packetDetector.threshold)
            plt.ylim([-1,2])
            plt.show()

    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests
    print 100 * (number_of_tests - errCount) / number_of_tests, "% SUCCESS RATE"

    plt.hist(delta, align='mid', rwidth=1)
    plt.title("PACKET ESTIMATION ERROR - "+str(number_of_tests)+" TESTS\n"
              "CORR_SIZE = "+str(pd_correlationSize)+" CORR_DELAY = "+str(pd_delay)+"\n"
              "CORR_DELAY_SECOND_CALCULATION = "+str(pd_delaySecondComputation))
    plt.xlabel("ERROR [IN SAMPLES]")
    plt.ylabel("NUMBER OF PACKETS")
    plt.show()