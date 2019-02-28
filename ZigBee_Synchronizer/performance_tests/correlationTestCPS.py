#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS2 import CFS2
from CFS import CFS
from CPS import CPS
import utils

import numpy as np
import matplotlib.pyplot as plt


if __name__ == "__main__":
    # Zigbee packet
    ##nbOfSamples = 256
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127  # 127
    freqOffset = 0.
    phaseOffset = 180.
    SNR = 6.

    # payload in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
    N = myPacket.I.__len__()

    # time vector
    maxTime = (1e-6 / sampleRate) * N
    timeStep = 1e-6 / sampleRate
    time = np.arange(0, maxTime, timeStep)
    # instantaneous phase error
    idealInstPhase = np.zeros(N)
    idealInstPhase[::] = 2 * np.pi * freqOffset * time[::] + phaseOffset * np.pi / 180

    # channel
    myChannel1 = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    myChannel2 = WirelessChannel(sampleRate, 0, 0, SNR)
    receivedSignal = myChannel1.receive(myPacket.IQ)
    idealReceivedSignal = myChannel2.receive(myPacket.IQ)

    ## receiver
    # CPS
    synchronizer2 = CPS(sampleRate)
    correctedSignal, phaseVector, sign = synchronizer2.costasLoop(850000, receivedSignal)
    # final instantaneous phase error estimated
    instPhase = np.zeros(N)
    instPhase[::] = phaseVector[::]


    ############################### PLOT ########################################################

    # correlation plot
    NormalizationCte = float(abs(np.correlate(idealReceivedSignal, idealReceivedSignal)))
    nbPointsToPlot = 100
    corrIdeal   = utils.correlate(idealReceivedSignal, idealReceivedSignal, nbPointsToPlot, NormalizationCte)
    corrRec     = utils.correlate(receivedSignal     , idealReceivedSignal, nbPointsToPlot, NormalizationCte)
    corrCorr    = utils.correlate(correctedSignal    , idealReceivedSignal, nbPointsToPlot, NormalizationCte)
    ideal, = plt.plot(corrIdeal, 'c--')
    rec, = plt.plot(corrRec, 'kx-')
    corr, = plt.plot(corrCorr, 'b')
    plt.legend([ideal, rec, corr], ['IDEAL', 'NON-CORRECTED', 'CPS'], loc=1)
    ideal.set_linewidth(4)
    corr.set_linewidth(2)
    plt.axhline(linewidth=2, color='g', y=0.6)
    plt.ylim(0, 1)
    plt.xlim(0, nbPointsToPlot)
    plt.grid(b=None, which='major', axis='y')
    plt.title("CORRELATION PLOT\n - SNR: " + str(SNR) + "dB - FreqOffset: " + str(freqOffset) + "Hz - PhaseOffset: " + str(phaseOffset) + "Deg")
    plt.ylabel("NORMALIZED AMPLITUDE")
    plt.xlabel("SAMPLES")
    plt.show()

    # plot phase differences
    plt.yticks(np.arange(-50, 50, 1))
    phaseDifference = np.unwrap(np.angle(correctedSignal)) - np.unwrap(np.angle(myPacket.IQ))
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