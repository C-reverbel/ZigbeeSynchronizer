from ZigBeePacket import ZigBeePacket
from WirelessChannel import WirelessChannel
from CFS2 import CFS2
from CFS import CFS
from CPS import CPS
import utils
import numpy as np
import matplotlib.pyplot as plt

# Zigbee packet
nbOfSamples = 256
sampleRate = 8
zigbeePayloadNbOfBytes = 20#127
freqOffset = 200.e3
phaseOffset = 250.
SNR = 10.

# Butterworth low-pass filter
cutoff = 3e6
fs = sampleRate * 1e6
order = 0

# payload in bytes, sample-rate in MHz
myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)
N = myPacket.I.__len__()

# time vector
maxTime = (1e-6 / sampleRate) * N
timeStep = 1e-6 / sampleRate
time = np.arange(0, maxTime, timeStep)

## CHANNEL
# sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
# receive signal and filter it (change filter order to ZERO to disable filtering)
receivedSignal = utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order)

# ideal received signal, no freq or phase offset
sync = CFS(sampleRate, nbOfSamples)
idealReceivedSignal = sync.compensateFrequencyAndPhase(freqOffset, phaseOffset, myChannel.receive(myPacket.IQ))

## CFS
# sample rate (MHz), number of samples - 2 to compute linear regression
synchronizer = CFS2(sampleRate, nbOfSamples, 4)
# estimate frequency and phase offset
phaseDifference = np.unwrap(np.angle(receivedSignal)) - np.unwrap(np.angle(myPacket.IQ))
freqOffsetEstimated, phaseOffsetEstimated = synchronizer.estimateFrequencyAndPhaseIterative(phaseDifference)
correctionVector = synchronizer.generatePhaseVector(freqOffsetEstimated, phaseOffsetEstimated)
# correct received signal with correctionVector
preCorrectedSignal = synchronizer.compensatePhase(correctionVector, receivedSignal)

## CPS
synchronizer2 = CPS(sampleRate)
correctedSignal, phaseVector, sign = synchronizer2.costasLoop(850000, preCorrectedSignal)
