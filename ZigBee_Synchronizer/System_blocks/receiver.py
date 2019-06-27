from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.TimeSync import TimeSynchronizer
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
from System_blocks.SymbolDetector import SymbolDetector
from System_blocks.PacketDetector import PacketDetector

import utils
import numpy as np
import matplotlib.pyplot as plt
from random import randint


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
            phaseOffset = 0.0
            SNR = 100.
        else:
            zigbeePayloadNbOfBytes = randint(5,127)
            freqOffset = float(randint(-200000,200000))
            phaseOffset = float(randint(0,360))
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
        N = myPacket.I.__len__()

        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate,  freqOffset, phaseOffset, SNR)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)

        ## Packet Detector
        packetDetector = PacketDetector(sampleRate)
        pd_index = packetDetector.detectPacket(receivedSignal)

        ## TimeSync
        timeSync = TimeSynchronizer(sampleRate)
        recPhase, ts_index = timeSync.getSyncPhase(receivedSignal, pd_index, 149)
        print pd_index, ts_index

        ## CFS
        idealPhase = np.unwrap(np.angle(myPacket.IQ[4:153])) # 149 points
        fit = np.polyfit(np.arange(0,149,1), recPhase - idealPhase, 1)
        freqEst =  fit[0] * 4000000 / np.pi

        CFS = CFS_direct(sampleRate, 149)
        preCorrectedSignal = CFS.compensateFrequencyAndPhase(freqEst,0.0,receivedSignal)

        ## CPS
        synchronizer = CPS(sampleRate)
        correctedSignal, phaseVector, _ = synchronizer.costasLoop(850000., preCorrectedSignal)

        if(DEBUG):
            plt.plot(myPacket.I[ts_index:ts_index + 100],'b')
            plt.plot(correctedSignal.real[ts_index:ts_index + 100],'r')
            plt.show()

    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests