#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_direct import CFS_direct
import utils
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Zigbee packet
    nbOfSamples = 1024
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 200e3
    phaseOffset = 50
    SNR = 10

    print "Zigbee payload size = " + str(zigbeePayloadNbOfBytes) + " bytes"
    print "Sample rate = " + str(sampleRate) + " MHz"
    print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
    print "Phase offset = " + str(phaseOffset) + " Degrees"
    print "SNR = " + str(SNR) + " dB"
    print "\n"

    accErrorsArray = []
    for k in range(30):
        # Filter requirements.
        order = k
        fs = 8e6  # sample rate, Hz
        cutoff = 2e6  # desired cutoff frequency of the filter, Hz

        accumulatedError = 0
        nbOfIterations = 100

        for i in range(nbOfIterations):
            # payload in bytes, sample-rate in MHz
            myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
            # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
            myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
            receivedSignal = utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order)
            # sample rate (MHz), number of samples - 2 to compute linear regression
            freqEstimator = CFS_direct(sampleRate, nbOfSamples)
            # estimate frequency and phase offset
            idealUnwrappedPhase = np.unwrap(np.angle(myPacket.IQ))
            receivedUnwrappedPhase = np.unwrap(np.angle(receivedSignal))
            phaseDifference = receivedUnwrappedPhase - idealUnwrappedPhase
            freqOffsetEstimated, phaseOffsetEstimated = freqEstimator.estimateFrequencyAndPhase(phaseDifference)
            preCorrectedSignal = freqEstimator.compensateFrequencyAndPhase(freqOffsetEstimated, phaseOffsetEstimated, receivedSignal)
            idealCorrectedSignal = freqEstimator.compensateFrequencyAndPhase(freqOffset, phaseOffset, receivedSignal)


            errorComparison = 100 * utils.calcAverageError(myPacket.IQ, preCorrectedSignal) / utils.calcAverageError(myPacket.IQ, idealCorrectedSignal)
            accumulatedError += errorComparison

            print "Estimated frequency offset = " + str(freqOffsetEstimated / 1000) + " kHz"
            print "Estimated phase offset = " + str(phaseOffsetEstimated) + " Degrees"
            print "Frequency estimation error = " + str((freqOffset - freqOffsetEstimated)) + " Hz"
            print "Phase estimation error = " + str((phaseOffset - phaseOffsetEstimated)) + " Degrees"
            print "Average error comparison (corrected signal / noisy signal) = " + \
                    str(errorComparison) + " %"
            print "\n"


            ## PLOT

            ## constellation plot: QPSK
            #receivedConstellation, = plt.plot(preCorrectedSignal.real[4::8], np.roll(preCorrectedSignal.imag, -4)[4::8], 'rx')
            #idealConstellation, = plt.plot(myPacket.I[4::8], np.roll(myPacket.Q, -4)[4::8], 'bo')
            #plt.axvline(x=0)
            #plt.axhline(y=0)
            #plt.legend([idealConstellation, receivedConstellation], ['IDEAL CONSTELLATION', 'CORRECTED CONSTELLATION'], loc=3)
            #receivedConstellation.set_linewidth(0.1)
            #plt.ylim(-2, 2)
            #plt.xlim(-2, 2)
            #plt.title("QPSK CONSTELLATION - IDEAL VS CORRECTED")
            #plt.show()
        accErrorsArray.append(accumulatedError / nbOfIterations)
        print "Final average error comparison (corrected signal / noisy signal) = " + str(accumulatedError / nbOfIterations) + " %",
        print " for k = " + str(k) + "\n"
    print accErrorsArray
    plt.plot(accErrorsArray)
    plt.show()
