from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
from System_blocks.TimeSync import TimeSynchronizer
import utils
import numpy as np
import matplotlib.pyplot as plt
from random import randint

if __name__ == "__main__":
    DEBUG = 1
    err = []
    errPlt = []
    number_of_tests = 3
    freqArray = [-200000.0, 0.0, 200000.0]
    for i in range(number_of_tests):
        # Zigbee packet
        sampleRate = 8
        zigbeePayloadNbOfBytes = 0
        if(DEBUG):
            freqOffset = freqArray[i]
            phaseOffset = 0.0
            SNR = 7000.
        else:
            freqOffset = 200000.#float(randint(-200000,200000))
            phaseOffset = float(randint(0,360))
            SNR = 1000.
        leadingNoiseSamples = 23
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
        # sts
        sts = TimeSynchronizer(sampleRate)
        recPhase = sts.getSyncPhase(receivedSignal, 0, 300)
        sts._estimateDelay(receivedSignal, 0, 300)

        plt.plot(sts.correlation)
    textArr = [str(j/1000) + " kHz" for j in freqArray]
    plt.legend(textArr,loc=3)
    plt.title("Correlated Signal - 25 points kernel")
    plt.xlabel("samples")
    plt.show()
