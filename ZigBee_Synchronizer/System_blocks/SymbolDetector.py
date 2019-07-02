from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.TimeSync import TimeSynchronizer
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
from System_blocks.PacketDetector import PacketDetector

import numpy as np
import matplotlib.pyplot as plt
from random import randint


class SymbolDetector:
    def __init__(self, sampleRate):
        self.kernel = [1, 1, 1]
        self.sampleRate = sampleRate

    def _discoverQuadrant(self):
        Ioffset = 0
        Qoffset = 0
        # search first 10 elements of both arrays for maximum index
        maxI = np.max((self.corrI[:6]))
        maxQ = np.max((self.corrQ[:6]))
        # discover whether I or Q comes first
        if maxI > maxQ:         # IQ
            Qoffset = 4
        else:                   # QI
            Ioffset = 4
        return Ioffset, Qoffset

    def detect(self, vector):
        N = (len(vector.real) - 4) / self.sampleRate
        self.corrI = np.correlate(vector.real, self.kernel, mode='full')
        self.corrQ = np.correlate(vector.imag, self.kernel, mode='full')

        self.satI = [1 if i > 0 else 0 for i in self.corrI]
        self.satQ = [1 if q > 0 else 0 for q in self.corrQ]
        # discover whether I or Q comes first
        Ioffset, Qoffset = self._discoverQuadrant()
        # Symbol converter
        tempI = 0
        tempQ = 0
        outI = []
        outQ = []
        for i in range(self.satI.__len__() - 4):
            # I
            tempI += 1 if self.satI[i + Ioffset] > 0 else -1
            if i % 8 == 0:
                outI.append(1 if tempI > 0 else 0)
                tempI = 0
            # Q
            tempQ += 1 if self.satQ[i + Qoffset] > 0 else -1
            if i % 8 == 0:
                outQ.append(1 if tempQ > 0 else 0)
                tempQ = 0
        # last point
        outI.append(1 if tempI > 0 else 0)
        outQ.append(1 if tempQ > 0 else 0)
        I_est = [-1 for i in range(N)]
        Q_est = [-1 for i in range(N)]
        for i in range(N):
            I_est[i] = int(outI[1+i])
            Q_est[i] = int(outQ[1+i])
        return I_est, Q_est


if __name__ == "__main__":
    DEBUG = 0
    errCount = 0
    number_of_tests = 10000
    for j in range(number_of_tests):
        # Zigbee packet
        sampleRate = 8
        zigbeePayloadNbOfBytes = 1
        if(DEBUG):
            freqOffset = 0.0
            phaseOffset = 0.0
            SNR = 700.
        else:
            freqOffset = 0.0#float(randint(-200000,200000))
            phaseOffset = 0.0#float(randint(0,360))
            SNR = 100.
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

        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate,  freqOffset, phaseOffset, SNR)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)

        ## Packet Detector ##
        ## =============== ##
        packetDetector = PacketDetector(sampleRate)
        pd_index = packetDetector.detectPacket(receivedSignal)
        ## TimeSync ##
        ## ======== ##
        timeSync = TimeSynchronizer(sampleRate)
        recPhase, ts_index = timeSync.getSyncPhase(receivedSignal, pd_index, 149)
        ## CFS ##
        ## === ##
        idealPhase = np.unwrap(np.angle(myPacket.IQ[4:153]))  # 149 points
        fit = np.polyfit(np.arange(0, 149, 1), recPhase - idealPhase, 1)
        freqEstimation = fit[0] * 4000000 / np.pi
        CFS = CFS_direct(sampleRate, 149)
        preCorrectedSignal = CFS.compensateFrequencyAndPhase(freqEstimation, 0.0, receivedSignal)
        ## CPS ##
        ## === ##
        synchronizer = CPS(sampleRate)
        correctedSignal, phaseVector, _ = synchronizer.costasLoop(100000., preCorrectedSignal)

        # Ideal I and Q messages
        I = [int(i) for i in myPacket.messageI]
        Q = [int(q) for q in myPacket.messageQ]
        N = I.__len__()

        SD = SymbolDetector(8)
        I_est, Q_est = SD.detect(correctedSignal[ts_index:])
        print SD._discoverQuadrant(),

        errI = 0
        errQ = 0

        for i in range(N):
            if I[i] != I_est[i] and I[i] != Q_est[i]:
                errI += 1
            #if Q[i] != Q_est[i]:
            #    errQ += 1
        print "TEST ", j+1,
        if errI or errQ:
            errCount += 1
            print "ERROR"
            print "I = ", errI, "/", N, "error"
            print "Q = ", errQ, "/", N, "error"
            print "I  = ", I
            print "Ie = ", I_est, '\n'
            print "Q  = ", Q
            print "Qe = ", Q_est, '\n'
        else:
            print "OK"

        if(DEBUG):
            plotMin = 0
            rang = 20
            plotMax = rang + plotMin
            plt.subplot(2, 1, 1)
            plt.plot(SD.corrI[plotMin:plotMax])
            plt.plot(SD.satI[plotMin:plotMax], 'x')
            plt.plot(receivedSignal.real[plotMin+leadingNoiseSamples:plotMax+leadingNoiseSamples], 'r')
            plt.axhline(y=0, color='k')
            #plt.plot(gardI[plotMin:plotMax],'-go')
            plt.subplot(2, 1, 2)
            plt.plot(SD.corrQ[plotMin:plotMax])
            plt.plot(SD.satQ[plotMin:plotMax], 'x')
            plt.plot(receivedSignal.imag[plotMin+leadingNoiseSamples:plotMax+leadingNoiseSamples], 'r')
            plt.axhline(y=0, color='k')
            #plt.plot(gardQ[plotMin:plotMax], '-go')
            plt.show()
        if errI or errQ or DEBUG:
            start = leadingNoiseSamples + 512
            lim = start + 100
            plt.axvline(x=pd_index-leadingNoiseSamples, linewidth=4, color='k')
            plt.plot(correctedSignal.real[leadingNoiseSamples:leadingNoiseSamples+100], linewidth=0.5, color='b')
            plt.plot(correctedSignal.imag[leadingNoiseSamples:leadingNoiseSamples+100], linewidth=0.5, color='r')
            plt.show()
            #plt.axvline(x=pd_index-leadingNoiseSamples, linewidth=4, color='k')
            plt.plot(correctedSignal.real[start:lim], linewidth=0.5, color='b')
            plt.plot(correctedSignal.imag[start:lim], linewidth=0.5, color='r')
            plt.show()
    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests

