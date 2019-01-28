#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS import CFS
import utils
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # Zigbee packet
    nbOfSamples = 1024
    sampleRate = 8
    zigbeePayloadNbOfBytes = 127
    freqOffset = 200e3
    phaseOffset = 10
    SNR = 10

    cutoff = 2e6
    fs = sampleRate * 1e6
    order = 5

    print "Zigbee payload size = " + str(zigbeePayloadNbOfBytes) + " bytes"
    print "Sample rate = " + str(sampleRate) + " MHz"
    print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
    print "Phase offset = " + str(phaseOffset) + " Degrees"
    print "SNR = " + str(SNR) + " dB"
    print "\n"

    # payload in bytes, sample-rate in MHz
    myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
    # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    receivedSignal = utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order)
    # sample rate (MHz), number of samples - 2 to compute linear regression
    freqEstimator = CFS(sampleRate, nbOfSamples)
    # estimate frequency and phase offset
    idealUnwrappedPhase = np.unwrap(np.angle(myPacket.IQ))
    receivedUnwrappedPhase = np.unwrap(np.angle(receivedSignal))
    phaseDifference = receivedUnwrappedPhase - idealUnwrappedPhase
    freqOffsetEstimated, phaseOffsetEstimated = freqEstimator.estimateFrequencyAndPhase(phaseDifference)
    preCorrectedSignal = freqEstimator.compensateFrequencyAndPhase(freqOffsetEstimated, phaseOffsetEstimated, receivedSignal)
    idealCorrectedSignal = freqEstimator.compensateFrequencyAndPhase(freqOffset, phaseOffset, receivedSignal)


