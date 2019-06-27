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
        self.kernel = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -1]
        self.Nk = self.kernel.__len__()
        self.goldDelay = 8#9
        self.computeRange = 128

    def getSyncPhase(self, vector, startSample, phaseSize):
        estDelay = self._estimateDelay(vector, startSample, self.computeRange)
        start = startSample + estDelay - self.goldDelay
        end = start + phaseSize
        return self.recPhase[start:end]

    def _estimateDelay(self, vector, startSample, size):
        self.recPhase = np.unwrap(np.angle(vector))
        self.correlation = []
        for i in range(size):
            self.correlation.append(np.correlate(self.recPhase[startSample + i:startSample + self.Nk + i], self.kernel))
        self.index = np.argmax(self.correlation)
        return self.index


if __name__ == "__main__":
    DEBUG = 1
    err = []
    errPlt = []
    number_of_tests = 3
    for i in range(number_of_tests):
        # Zigbee packet
        sampleRate = 8
        zigbeePayloadNbOfBytes = 0
        if(DEBUG):
            freqOffset = 0.0
            phaseOffset = 0.0
            SNR = 7000.
        else:
            freqOffset = 200000.#float(randint(-200000,200000))
            phaseOffset = float(randint(0,360))
            SNR = 1000.
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

        # sts
        sts = TimeSynchronizer(sampleRate)
        recPhase = sts.getSyncPhase(receivedSignal, startSample, 149)
        estimate = sts._estimateDelay(receivedSignal, startSample, 128)
        sts_start = startSample
        sts_end = sts_start + 128

        gold = 9
        idealPhase = np.unwrap(np.angle(myPacket.IQ[4:132 + 21]))

        if(DEBUG):
            plt.subplot(3, 1, 1)
            plt.plot(packetD, linewidth=0.5,color='r')
            plt.subplot(3, 1, 2)
            plt.plot(sts.recPhase[:NpkD])
            plt.axvline(x=sts_start, color='k')
            plt.axvline(x=sts_start+estimate, color='r')
            plt.axvline(x=sts_end, color='k')
            plt.subplot(3, 1, 3)
            plt.plot(sts.correlation,'-x')
            plt.axvline(x=sts.index, color='r')
            plt.show()

            plt.subplot(3, 1, 1)
            plt.plot(sts.recPhase[sts_start:sts_end],'-x')
            plt.axvline(x=estimate, color='r')
            plt.subplot(3, 1, 2)
            plt.plot(recPhase)
            plt.plot(idealPhase)
            plt.subplot(3, 1, 3)
            plt.plot(idealPhase - recPhase)
            plt.show()

        fit = np.polyfit(np.arange(0,149,1), recPhase - idealPhase, 1)
        freqEst =  fit[0] * 4000000 / np.pi
        err.append(int(freqOffset - freqEst))
        if(abs(err[-1]) > 1500):
            print err[-1]
    errCount = 0
    for i in err:
        if(abs(i) > 1500):
            errCount += 1
    print errCount


    # print setup
    pltX = [-2000,-1500,-1000,-500,0,500,1000,1500,2000]
    for i in range(pltX.__len__()-1):
        errPlt.append(sum(j >= pltX[i] and j < pltX[i+1] for j in err))
    errPlt.append(0)
    xx = np.arange(len(pltX))

    if not DEBUG:
        plt.bar(xx,errPlt,align='edge',width=1)
        plt.xticks(xx, pltX)
        plt.title("Frequency estimation error histogram for " + str(number_of_tests) + " tests\n"
                " SNR = " + str(SNR) + " dB, dF =" + str(freqOffset / 1000) + " kHz")
        plt.xlabel("Frequency error")
        plt.ylabel("Occurrences")
        plt.xlim(0,8)
        plt.ylim(0,400)
        plt.grid(axis='y')
        plt.show()

    temp = sum(abs(i) > 2000 for i in err)
    print "Points with error greather than 2000 Hz: ", temp, "percentage:", 100 * temp/number_of_tests, "%"
    stringg = [str(pltX[i])+" <-> "+str(pltX[i+1])+" = "+str(100*float(errPlt[i])/number_of_tests)+" %" for i in range(len(pltX)-1)]
    for i in range(len(stringg)):
        print stringg[i]