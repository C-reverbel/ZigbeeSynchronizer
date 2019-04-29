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
        self.kernel = np.unwrap(np.angle(packet.IQ[4:37]))

    def estimateDelay(self, vector):
        recPhase = np.unwrap(np.angle(vector))
        correlation = np.correlate(recPhase, self.kernel, mode='full')
        index = np.argmax(correlation[150:280])
        return index + 150 - 167


if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 50
    freqOffset = 200000.0
    phaseOffset = 70.0
    SNR = 9.
    leadingNoiseSamples = 0
    trailingNoiseSamples = 0

    # Butterworth low-pass filter
    cutoff = 3e6
    fs = sampleRate * 1e6
    order = 0

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
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)

    totalFail = 0
    nbOfTests = 200
    tol = 1
    for i in range(nbOfTests):
        leadingNoiseSamples = randint(0, 30)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = utils.butter_lowpass_filter(
                            myChannel.receive(myPacket.IQ,
                                              leadingNoiseSamples,
                                              trailingNoiseSamples),
                            cutoff, fs, order)

        sts = TimeSynchronizer(sampleRate)
        estimate = sts.estimateDelay(receivedSignal)


        print "expected  = ", leadingNoiseSamples, \
            "estimated = ", estimate,
        if(estimate > leadingNoiseSamples+tol or estimate < leadingNoiseSamples-tol):
            totalFail = totalFail+1
            print "NOK"
        else:
            print "OK"


    print "Total fails = ", totalFail, " of ", nbOfTests