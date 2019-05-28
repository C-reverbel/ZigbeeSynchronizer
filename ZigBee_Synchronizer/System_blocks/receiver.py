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


if __name__ == "__main__":
    DEBUG = 0
    err = []
    errCount = 0
    number_of_tests = 100
    for j in range(number_of_tests):
        # Zigbee packet
        sampleRate = 8
        if(DEBUG):
            zigbeePayloadNbOfBytes = 10
            freqOffset = 200000.0
            phaseOffset = 0.
            SNR = 10.
        else:
            zigbeePayloadNbOfBytes = randint(5,127)
            freqOffset = float(randint(-200000,200000))
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
        N = myPacket.I.__len__()

        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate,  freqOffset, phaseOffset, SNR)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)

        # packet detector
        packetD_offset = np.zeros(randint(157, 185))
        packetD_periode = np.ones(randint(150,400))
        startSample = packetD_offset.__len__() + packetD_periode.__len__()
        packetD_end = np.zeros(1028 - startSample)
        packetD = np.append(np.append(packetD_offset, packetD_periode), packetD_end)
        NpkD = packetD.__len__()

        ## TimeSync
        sts = TimeSynchronizer(sampleRate)
        recPhase = sts.getSyncPhase(receivedSignal, startSample, 149)

        ## CFS
        idealPhase = np.unwrap(np.angle(myPacket.IQ[4:153])) # 149 points
        fit = np.polyfit(np.arange(0,149,1), recPhase - idealPhase, 1)
        freqEst =  fit[0] * 4000000 / np.pi

        CFS = CFS_direct(sampleRate, 149)
        preCorrectedSignal = CFS.compensateFrequencyAndPhase(freqEst,0.0,receivedSignal)

        ## CPS
        synchronizer = CPS(sampleRate)
        correctedSignal, phaseVector, _ = synchronizer.costasLoop(1000., preCorrectedSignal)

        ## Symbol Detector
        SD = SymbolDetector(sampleRate)
        I_est, Q_est = SD.detect(correctedSignal[1536:]) # take only the payload


        # PRINTS
        # Ideal I and Q messages (payload only)
        I = [int(i) for i in myPacket.messageI[192:]]
        Q = [int(q) for q in myPacket.messageQ[192:]]


        if(DEBUG):
            plt.plot(myPacket.I[100:200])
            plt.plot(correctedSignal.real[100:200])
            plt.show()

        errI = 0
        errQ = 0

        for i in range(len(I)):
            if I[i] != I_est[i]:
                errI += 1
            if Q[i] != Q_est[i]:
                errQ += 1
        print "TEST ", j + 1, "DF = ", freqOffset, "PAYLOAD = ", zigbeePayloadNbOfBytes
        if errI or errQ:
            errCount += 1
            print "I = ", errI, "/", N, "error"
            print "Q = ", errQ, "/", N, "error"
            print "I  = ", I
            print "Ie = ", I_est, '\n'
            print "Q  = ", Q
            print "Qe = ", Q_est, '\n'
    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests