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
        self.kernel = np.unwrap(np.angle(packet.IQ[10:15]))#tot = 5
        #self.kernel = np.unwrap(np.angle(packet.IQ[5:37]))#tot = 32
        print self.kernel.__len__()
        plt.plot(self.kernel, '-x')
        plt.show()

    def estimateDelay(self, vector):
        recPhase = np.unwrap(np.angle(vector))
        self.correlation = np.correlate(recPhase, self.kernel, mode='full')
        #start = 150
        start = 140
        range = 35
        #range = 100
        index = np.argmax(self.correlation[start:start + range])
        plt.plot(sts.correlation[:start+range])
        plt.axvline(x=start)
        plt.axvline(x=start+range)
        plt.axvline(x=index + start, color='r')
        plt.show()

        return index + start - 142
        #return index + start - 167 # 150 - 200


if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 0
    freqOffset = -200000.0
    phaseOffset = 0.0
    SNR = 7.
    leadingNoiseSamples = 14
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

    nbOfTests = 5
    totalFail = 0
    tol = 1
    for i in range(nbOfTests):
        #leadingNoiseSamples = randint(0, 14)
        #leadingNoiseSamples = randint(0, 55)
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




    #plt.plot(np.unwrap(np.angle(myPacket.IQ[4:132])))
    #plt.show()

    #angle = np.arange(0.0,1.0,0.001)
    #approx = 1.0797 * angle - 0.288 * angle ** 2 - 0.005
    #arc = np.arctan(angle)
    #err = arc-approx
    #plt.subplot(2,1,1)
    #plt.plot(arc)
    #plt.plot(approx)
    #plt.subplot(2,1,2)
    #plt.plot(err)
    #plt.show()
    #
    #print np.sum(abs(err))
