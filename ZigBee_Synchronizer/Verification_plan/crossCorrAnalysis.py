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


if __name__ == "__main__":
    # Zigbee packet
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 10.
    phaseOffset =160.
    SNR = 1000.

    leadingNoiseSamples = 0
    trailingNoiseSamples = 0

    # Butterworth low-pass filter
    cutoff = 2.5e6
    fs = sampleRate * 1e6
    order = 0

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
    receivedSignal = utils.butter_lowpass_filter(myChannel1.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples), cutoff, fs, order)
    idealReceivedSignal = myChannel2.receive(myPacket.IQ)

    N_ext = receivedSignal.real.__len__()
    ## receiver
    # CPS
    synchronizer2 = CPS(sampleRate)
    correctedSignal, phaseVector, correctedBits = synchronizer2.costasLoop(850000, receivedSignal)
    # final instantaneous phase error estimated
    instPhase = np.zeros(N_ext)
    instPhase[::] = phaseVector[::]

    # ## demodulated signals
    # receivedBits = np.sign(receivedSignal.real) + 1j * np.sign(receivedSignal.imag)
    # idealBits = np.sign(myPacket.IQ.real) + 1j * np.sign(myPacket.IQ.imag)
    # idealNoisyBits = np.sign(idealReceivedSignal.real) + 1j * np.sign(idealReceivedSignal.imag)

    ############################### PLOT ########################################################

    # # correlation plot
    # NormalizationCte = float(abs(np.correlate(myPacket.IQ, myPacket.IQ)))
    # nbPointsToPlot = 20
    # corrIdeal   = utils.correlate(idealReceivedSignal, myPacket.IQ, nbPointsToPlot, NormalizationCte)
    # corrRec     = utils.correlate(receivedSignal     , myPacket.IQ, nbPointsToPlot, NormalizationCte)
    # corrCorr    = utils.correlate(correctedSignal    , myPacket.IQ, nbPointsToPlot, NormalizationCte)
    # ideal, = plt.plot(corrIdeal, 'c--')
    # rec, = plt.plot(corrRec, 'kx-')
    # corr, = plt.plot(corrCorr, 'b')
    # plt.legend([ideal, rec, corr], ['IDEAL', 'NON-CORRECTED', 'CPS'], loc=1)
    # ideal.set_linewidth(4)
    # corr.set_linewidth(2)
    # plt.axhline(linewidth=2, color='g', y=0.95)
    # plt.ylim(0, 1)
    # plt.xlim(0, nbPointsToPlot)
    # plt.grid(b=None, which='major', axis='y')
    # plt.title("CORRELATION PLOT\n - SNR: " + str(SNR) + "dB - FreqOffset: " + str(freqOffset) + "Hz - PhaseOffset: " + str(phaseOffset) + "Deg")
    # plt.ylabel("NORMALIZED AMPLITUDE")
    # plt.xlabel("SAMPLES")
    # plt.show()

    # bits correlation
    NormalizationCte = float(abs(np.correlate(myPacket.I, myPacket.I)))
    nbPointsToPlot = 100
    corrIdeal = utils.correlate(myPacket.I, myPacket.I, nbPointsToPlot, NormalizationCte)
    recII  = utils.correlate(receivedSignal.real, myPacket.I,nbPointsToPlot, NormalizationCte)
    recIQ  = utils.correlate(receivedSignal.real, myPacket.Q,nbPointsToPlot, NormalizationCte)
    corrII = utils.correlate(correctedSignal.real, myPacket.I, nbPointsToPlot, NormalizationCte)
    corrIQ = utils.correlate(correctedSignal.real, myPacket.Q, nbPointsToPlot, NormalizationCte)
    ideal, = plt.plot(corrIdeal, 'c--')
    rii, = plt.plot(recII, 'rx-')
    riq, = plt.plot(recIQ, 'bx-')
    cii, = plt.plot(corrII, 'r')
    ciq, = plt.plot(corrIQ, 'b')
    plt.legend([ideal, rii, riq, cii, ciq], ['IDEAL', 'REC I-I', 'REC I-Q', 'CPS I-I', 'CPS I-Q'], loc=1)
    ideal.set_linewidth(4)
    rii.set_linewidth(0.5)
    riq.set_linewidth(0.5)
    plt.axhline(linewidth=2, color='g', y=0.95)
    plt.ylim(0, 1)
    plt.xlim(0, nbPointsToPlot)
    plt.grid(b=None, which='major', axis='y')
    plt.title(
        "CORRELATION PLOT - I and Q\n - SNR: " + str(SNR) + "dB - FreqOffset: " + str(freqOffset) + "Hz - PhaseOffset: " + str(
            phaseOffset) + "Deg")
    plt.ylabel("NORMALIZED AMPLITUDE")
    plt.xlabel("SAMPLES")
    plt.show()

    # # time domain plot
    # offset = 100
    # numberPoints = 100
    # samples = range(offset, offset + numberPoints)
    # I_rec, = plt.plot(samples, receivedSignal.real[offset:offset + numberPoints], 'b')
    # Q_rec, = plt.plot(samples, receivedSignal.imag[offset:offset + numberPoints], 'r')
    # I_ideal, = plt.plot(samples, idealReceivedSignal.real[offset:offset + numberPoints], 'c--')
    # Q_ideal, = plt.plot(samples, idealReceivedSignal.imag[offset:offset + numberPoints], '--', color='orange')
    # plt.legend([I_ideal, Q_ideal, I_rec, Q_rec], \
    #            ['I', 'Q', 'I REC', 'Q REC'], loc=3)
    # plt.title("TIME DOMAIN IN-PHASE SIGNAL\n - SNR: " + str(SNR) + "dB - FreqOffset: " + str(freqOffset) + "Hz - PhaseOffset: " + str(phaseOffset) + "Deg")
    # plt.ylabel("Amplitude (Volts)")
    # plt.xlabel("samples")
    # plt.axhline(y=0, color='k')
    # plt.show()
    #
    # plot phase differences
    plt.yticks(np.arange(-50, 50, 1))
    if leadingNoiseSamples == 0 and trailingNoiseSamples == 0:
        phaseDifference = np.unwrap(np.angle(correctedSignal)) - np.unwrap(np.angle(myPacket.IQ))
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


    #samplToPlot = 20
    #plt.plot(time[0:samplToPlot]*1000, myPacket.I[0:samplToPlot], 'x--')
    #plt.plot(time[0:samplToPlot] * 1000, myPacket.Q[0:samplToPlot], 'o--')
    #for p in np.arange(0, samplToPlot * 125e-6, 125e-6):
    #    plt.axvline(linewidth=1, color='g', x=p)
    #    print p
    #plt.show()
