from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.CFS_iterative import CFS_iterative
from System_blocks.CPS import CPS
import utils
import numpy as np

N_TEST = 0

def to_bit(vector, window = 8):
    bit_vector = []
    vector.imag = np.roll(vector.imag, -4)
    vector = vector[0:-4]

    for i in range(0, len(vector), window):
        bit_vector.append(int((np.sign(np.sum(vector.real[i:i+window])) + 1) / 2))
        bit_vector.append(int((np.sign(np.sum(vector.imag[i:i+window])) + 1) / 2))

    return bit_vector

def do_check(ideal, received):
    '''
    Check the ideal data transmitted over corrected received data
    '''
    errNum = 0
    i_bits = to_bit(ideal)
    r_bits  = to_bit(received)

    errNum = np.sum([1 if i_bits[i] != r_bits[i] else 0 for i in range(len(i_bits))])
    l = 0
    for i in range(len(i_bits)):
        if i_bits[i] != r_bits[i] and (i - l) < 32 and l != 0:
            print "Vai dar biru!", l, i
            l = i

    return 100 * float(errNum) / len(i_bits)

def do_report():
    print "Zigbee payload size = " + str(zigbeePayloadNbOfBytes) + " bytes"
    print "Sample rate = " + str(sampleRate) + " MHz"
    print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
    print "Phase offset = " + str(phaseOffset) + " Degrees"
    print "SNR = " + str(SNR) + " dB"
    print "\n"
    
    print "CFS estimated frequency and phase offset"
    print "Frequency = " + str(freqOffsetEstimated[-1])
    print "Phase = " + str(phaseOffsetEstimated[-1])
    print "Frequency Error = " + str(freqOffsetEstimated[-1] - freqOffset)
    print "Phase Error = " + str(phaseOffsetEstimated[-1] - phaseOffset) + "\n"

def do_test(nbOfSamples, payloadSize, freqOffset, phaseOffset, snr, coff, sampleRate = 8):
    '''
    Do a integrity test with the parameters passed
    '''
    global N_TEST
    N_TEST += 1

    # Butterworth low-pass filter
    cutoff = 2e6
    fs = sampleRate * 1e6
    order = 0
    numTests = 128
    err = 0.0

    for i in range(numTests):
        myPacket = ZigBeePacket(payloadSize, sampleRate)
        N = myPacket.I.__len__()

        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, snr)
        # receive signal and filter it (change filter order to ZERO to disable filtering)
        receivedSignal = utils.butter_lowpass_filter(myChannel.receive(myPacket.IQ), cutoff, fs, order)

        ## CFS
        # sample rate (MHz), number of samples - 2 to compute linear regression
        synchronizer = CFS_iterative(sampleRate, nbOfSamples, 4)
        # estimate frequency and phase offset
        phaseDifference = np.unwrap(np.angle(receivedSignal)) - np.unwrap(np.angle(myPacket.IQ))
        freqOffsetEstimated, phaseOffsetEstimated = synchronizer.estimateFrequencyAndPhaseIterative(phaseDifference)
        correctionVector = synchronizer.generatePhaseVector(freqOffsetEstimated, phaseOffsetEstimated)
        # correct received signal with correctionVector
        preCorrectedSignal = synchronizer.compensatePhase(correctionVector, receivedSignal)

        ## CPS
        synchronizer2 = CPS(sampleRate)
        correctedSignal, phaseVector, signVector = synchronizer2.costasLoop(coff, preCorrectedSignal)

        ################################################### PLOT
        # time vector
        #maxTime = (1e-6 / sampleRate) * N
        #timeStep = 1e-6 / sampleRate
        #time = np.arange(0, maxTime, timeStep)

        # ideal received signal, no freq or phase offset
        #sync = CFS(sampleRate, nbOfSamples)
        #idealReceivedSignal = sync.compensateFrequencyAndPhase(freqOffset, phaseOffset, myChannel.receive(myPacket.IQ))

        #idealReceivedSignal.imag = np.roll(idealReceivedSignal.imag, -4)
        #preCorrectedSignal.imag = np.roll(preCorrectedSignal.imag, -4)
        correctedSignal.imag = np.roll(correctedSignal.imag, -4)

        err += do_check(myPacket.IQ, correctedSignal)

    print "Test", N_TEST, "Err > %.2f %%" % (err / numTests)


def main():
    # Zigbee packet
    # nbOfSamples = 256
    # sampleRate = 8
    # zigbeePayloadNbOfBytes = 127
    # freqOffset = 200e3
    # phaseOffset = 20
    # SNR = 10
    # Butterworth low-pass filter
    # cutoff = 2e6
    # fs = sampleRate * 1e6
    # order = 0
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 850e3)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 100e3)
    exit()
    print "\n## sn = 256, fo = 200e3, po = 20, snr = 15"
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 100e3)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 5e3)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 500)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 100)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 50)
    print "\n## sn = 128, fo = 200e3, po = 20, snr = 15"
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 100e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 5e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 500)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 100)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 15., coff = 50)
    print "\n## sn = 256, fo = 200e3, po = 20, snr = 10"
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 100e3)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 5e3)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 500)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 100)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 50)
    print "\n## sn = 128, fo = 200e3, po = 20, snr = 10"
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 100e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 5e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 500)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 100)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 10., coff = 50)
    print "\n## sn = 256, fo = 200e3, po = 20, snr = 8"
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 1e6)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 5e3)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 500)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 100)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 50)
    print "\n## sn = 128, fo = 200e3, po = 20, snr = 8"
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 850e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 100e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 1e6)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 5e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 500)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 100)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 8., coff = 50)

    print "\n## sn = 256, fo = 200e3, po = 20, snr = 5"
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 1e6)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 5e3)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 500)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 100)
    do_test(nbOfSamples = 256, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 50)
    print "\n## sn = 128, fo = 200e3, po = 20, snr = 5"
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 850e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 100e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 1e6)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 5e3)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 500)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 100)
    do_test(nbOfSamples = 128, payloadSize = 127, freqOffset = 200e3, phaseOffset = 20, snr = 5., coff = 50)

if __name__ == '__main__':
    main()