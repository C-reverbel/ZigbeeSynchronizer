#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
import sys
sys.path.append('../')

from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CPS import CPS
import utils

import numpy as np
import matplotlib.pyplot as plt
from random import randint


if __name__ == "__main__":
    DEBUG = 0
    errCount = 0
    number_of_tests = 1000
    for j in range(number_of_tests):
        # Zigbee packet
        sampleRate = 8
        if(DEBUG):
            zigbeePayloadNbOfBytes = 127
            freqOffset = 1000.
            phaseOffset = 0.
            SNR = 7.
        else:
            zigbeePayloadNbOfBytes = 127
            freqOffset = 1000.
            phaseOffset = float(randint(0,360))
            SNR = 9.

        leadingNoiseSamples = 0
        trailingNoiseSamples = 0

        threshold = 0.9

        # payload in bytes, sample-rate in MHz
        myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
        N = myPacket.I.__len__()

        # channel
        myChannel1 = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
        receivedSignal = myChannel1.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)
        N_ext = receivedSignal.real.__len__()
        ## receiver
        # CPS
        synchronizer2 = CPS(sampleRate)
        correctedSignal, phaseVector, correctedBits = synchronizer2.costasLoop(850000., receivedSignal)
        # final instantaneous phase error estimated
        instPhase = np.zeros(N_ext)
        instPhase[::] = phaseVector[::]

        # bits correlation
        NormalizationCte = float(abs(np.correlate(myPacket.I, myPacket.I)))
        nbPointsToPlot = 20
        if(DEBUG):
            corrIdeal = utils.correlate(myPacket.I, myPacket.I, nbPointsToPlot, NormalizationCte)
            recII     = utils.correlate(receivedSignal.real, myPacket.I,nbPointsToPlot, NormalizationCte)
            recIQ     = utils.correlate(receivedSignal.real, myPacket.Q,nbPointsToPlot, NormalizationCte)
        corrII = utils.correlate(correctedSignal.real, myPacket.I, nbPointsToPlot, NormalizationCte)
        corrIQ = utils.correlate(correctedSignal.real, myPacket.Q, nbPointsToPlot, NormalizationCte)

        # check synchronization
        maxII = np.max(corrII)
        maxIQ = np.max(corrIQ)
        maxMax = np.maximum(maxII,maxIQ)
        if(maxMax < threshold): errCount += 1

        if(DEBUG):
            # time vector
            maxTime = (1e-6 / sampleRate) * N
            timeStep = 1e-6 / sampleRate
            time = np.arange(0, maxTime, timeStep)

            print synchronizer2.C1, synchronizer2.C2
            plotStart = 20000
            plotRange = 200


            plt.plot(correctedSignal.real[plotStart:plotStart+plotRange])
            plt.plot(myPacket.IQ.real[plotStart:plotStart + plotRange])
            plt.show()


            # instantaneous phase error
            idealInstPhase = np.zeros(N)
            idealInstPhase[::] = 2 * np.pi * freqOffset * time[::] + phaseOffset * np.pi / 180

            ideal, = plt.plot(corrIdeal, 'c--')
            rii, = plt.plot(recII, 'rx-')
            riq, = plt.plot(recIQ, 'bx-')
            cii, = plt.plot(corrII, 'r')
            ciq, = plt.plot(corrIQ, 'b')
            plt.legend([ideal, rii, riq, cii, ciq], ['IDEAL', 'REC I-I', 'REC I-Q', 'CPS I-I', 'CPS I-Q'], loc=1)
            ideal.set_linewidth(4)
            rii.set_linewidth(0.5)
            riq.set_linewidth(0.5)
            plt.axhline(linewidth=2, color='g', y=threshold)
            plt.ylim(0, 1)
            plt.xlim(0, nbPointsToPlot)
            plt.grid(b=None, which='major', axis='y')
            plt.title(
                "CORRELATION PLOT - I and Q\n - SNR: " + str(SNR) + "dB - FreqOffset: " + str(freqOffset) + "Hz - PhaseOffset: " + str(
                    phaseOffset) + "Deg")
            plt.ylabel("NORMALIZED AMPLITUDE")
            plt.xlabel("SAMPLES")
            plt.show()

            # plot phase differences
            plt.yticks(np.arange(-50, 50, 1))
            if leadingNoiseSamples == 0 and trailingNoiseSamples == 0:
                phaseDifference = np.unwrap(np.angle(correctedSignal[:N])) - np.unwrap(np.angle(myPacket.IQ))
            else:
                phaseDifference = np.unwrap(np.angle(correctedSignal[leadingNoiseSamples:-trailingNoiseSamples])) - np.unwrap(np.angle(myPacket.IQ))
            phaseNoiseCPS, = plt.plot(1e3 * time, phaseDifference * 2 / np.pi, 'b')
            phaseNoiseCPS.set_linewidth(0.5)
            plt.title("PHASE ERROR\n - SNR: " + str(SNR) + "dB - FreqOffset: " + str(freqOffset) + "Hz - PhaseOffset: " + str(phaseOffset) + "Deg")
            plt.ylabel("PHASE (n * pi / 2)")
            plt.xlabel("TIME (ms)")
            plt.xlim(0, 1e3 * time[-1])
            plt.grid(b=None, which='major', axis='both')
            plt.show()

            # plot CPS phase output
            lim = N
            estimate, = plt.plot(time[:lim] * 1000, instPhase[:lim], 'b')
            ref,      = plt.plot(time[:lim] * 1000, idealInstPhase[:lim], 'c--')
            plt.legend([estimate, ref], ['MEASURED', 'IDEAL'], loc=2)
            ref.set_linewidth(4)
            plt.grid(b=None, which='major', axis='both')
            plt.title("DELTA_PHI\n - SNR: " + str(SNR) + "dB - FreqOffset: " + str(freqOffset) + "Hz - PhaseOffset: " + str(phaseOffset) + "Deg")
            plt.ylabel("INSTANTANEOUS PHASE (rad)")
            plt.xlabel("TIME (ms)")
            plt.show()
        else:
            print "TEST ", j+1,
            if(maxMax < threshold): print " -- ERROR"
            else: print ""

    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests


