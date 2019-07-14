from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.TimeSync import TimeSynchronizer
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
from System_blocks.PacketDetector import PacketDetector

import numpy as np
import matplotlib.pyplot as plt
from random import randint


class PhaseSymbolDetector:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        self.phaseList = [-180, -90, 0, 90, 180]

    def detect(self, vector):
        # get input unwrapped phase
        recPhase = np.unwrap(np.angle(vector))
        self.recPhaseUnderSample = recPhase[0:-1:4]
        recBits = [1, 1]

        ## convert phase to bits
        offset = 1
        for i in range(len(self.recPhaseUnderSample) - 3):
            temp = self.recPhaseUnderSample[i+offset:i+offset+3]
            recBits.append(self._phaseToBit(temp, recBits[i]))
        return recBits

    def _phaseToBit(self, vect, start):
        # converts 3-point phase vector to bit
        # check for rising or falling
        if vect[0] > vect[1] > vect[2] or vect[0] < vect[1] < vect[2]:
            return 1 - start
        # check for maximum or minimum
        if (vect[1] > vect[0] and vect[1] > vect[2]) or (vect[1] < vect[0] and vect[1] < vect[2]):
            return start



if __name__ == "__main__":
    DEBUG = 0
    errCount = 0
    number_of_tests = 100
    for j in range(number_of_tests):
        sampleRate = 8
        zigbeePayloadNbOfBytes = 127
        if(DEBUG):
            freqOffset = 0.0
            phaseOffset = 0.0
            SNR = 700.
        else:
            freqOffset = float(randint(-200000,200000))
            phaseOffset = float(randint(0,360))
            SNR = 7.
        leadingNoiseSamples = randint(1,20) * 50
        trailingNoiseSamples = 0

        if(DEBUG):
            print "Zigbee payload size = " + str(zigbeePayloadNbOfBytes) + " bytes"
            print "Sample rate = " + str(sampleRate) + " MHz"
            print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
            print "Phase offset = " + str(phaseOffset) + " Degrees"
            print "SNR = " + str(SNR) + " dB"
            print "\n"

        ## PACKET ##
        ## ====== ##
        # payload in bytes, sample-rate in MHz
        myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
        ## CHANNEL ##
        ## ======= ##
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
        polyfitSize = 149
        timeSync = TimeSynchronizer(sampleRate)
        recPhase, ts_index = timeSync.getSyncPhase(receivedSignal, pd_index, polyfitSize)
        ## CFS ##
        ## === ##
        idealPhase = np.unwrap(np.angle(myPacket.IQ[4:4+polyfitSize]))  # 149 points
        fit = np.polyfit(np.arange(0, polyfitSize, 1), recPhase - idealPhase, 1)
        freqEstimation = fit[0] * 4000000 / np.pi
        CFS = CFS_direct(sampleRate, polyfitSize)
        preCorrectedSignal = CFS.compensateFrequencyAndPhase(freqEstimation, 0.0, receivedSignal)
        ## CPS ##
        ## === ##
        synchronizer = CPS(sampleRate)
        correctedSignal, phaseVector, _ = synchronizer.costasLoop(100000., preCorrectedSignal)
        ## PSD ##
        ## === ##
        phaseSymbolDetector = PhaseSymbolDetector(8)
        recBits = phaseSymbolDetector.detect(correctedSignal[ts_index+128:])


        ## VERIFICATION
        err = 0
        idealBits = [int(i) for i in myPacket.messageInChip[len(myPacket.messageInChip) - len(recBits):]]

        # check for error
        for i in range(len(idealBits)):
            if not idealBits[i] == recBits[i]:
                err = 1

        if err or DEBUG:
            print [recBits[i*32:i*32 + 32] for i in range(len(recBits) / 32)]
            print [idealBits[i*32:i*32 + 32] for i in range(len(idealBits) / 32)]
            print "FREQ = ", freqOffset, freqEstimation, "|", freqOffset - freqEstimation
            print "TIMING = ", leadingNoiseSamples, ts_index, "|", leadingNoiseSamples - ts_index

        print "TEST ", j+1,
        if err:
            errCount += 1
            print "ERROR"
        else:
            print "OK"

        if err or DEBUG:
            idealUndersamplePhase = np.unwrap(np.angle(myPacket.IQ[0:-1:4]))
            #print len(phaseSymbolDetector.recPhaseUnderSample)
            plotOffset = len(idealUndersamplePhase) - len(phaseSymbolDetector.recPhaseUnderSample)
            plotMin = 0
            rang = 8440
            plotMax = plotMin + rang

            plt.subplot(2,1,1)
            plt.plot(np.unwrap(np.angle(myPacket.IQ)), 'b')
            plt.plot(np.unwrap(np.angle(correctedSignal[leadingNoiseSamples:])), 'r')
            plt.subplot(2,1,2)
            plt.plot(phaseVector)
            plt.show()

    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests

