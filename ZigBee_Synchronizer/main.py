#                   _________                         _____                             _____
#                  |         |                       |     |                           |     |
#  myPacket.IQ --> | CHANNEL | -- receivedSignal --> | CFS | -- preCorrectedSignal --> | CPS | --> correctedSignal
#                  |_________|                       |_____|                           |_____|
#
from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS import CFS
import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    nbOfSamples = 128
    sampleRate = 8
    freqOffset = 200e3
    phaseOffset = 10
    SNR = 10

    # 2 bytes payload, 8 MHz sample-rate
    myPacket = ZigBeePacket(127, sampleRate)

    # sample rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
    myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
    receivedSignal = myChannel.receive(myPacket.IQ)

    # sample rate (MHz), number of samples - 2 to compute linear regression
    freqEstimator = CFS(sampleRate, nbOfSamples)
    phaseDifference = np.unwrap(np.angle(receivedSignal)) - np.unwrap(np.angle(myPacket.IQ))
    freqOffsetEstimated, phaseOffsetEstimated = \
        freqEstimator.estimateFrequencyAndPhase(phaseDifference)
    preCorrectedSignal = \
        freqEstimator.compensateFrequencyAndPhase(freqOffsetEstimated, phaseOffsetEstimated, receivedSignal)
