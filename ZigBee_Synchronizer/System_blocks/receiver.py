from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.TimeSync import TimeSynchronizer
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
from System_blocks.SymbolDetector import SymbolDetector
from System_blocks.SymbolDecoder import SymbolDecoder
from System_blocks.PacketDetector import PacketDetector

import utils
import numpy as np
import matplotlib.pyplot as plt
from random import randint

class ZigbeeReceiver:
    def __init__(self, sampleRate):
        self.sampleRate = sampleRate
        self.phaseEstimationSize = 149
        self.myPacket = ZigBeePacket(0, self.sampleRate)

    def receive(self, rawZigbeePacket):
        ## Packet Detector ##
        ## =============== ##
        packetDetector = PacketDetector(self.sampleRate)
        pd_index = packetDetector.detectPacket(rawZigbeePacket)
        ## TimeSync ##
        ## ======== ##
        timeSync = TimeSynchronizer(self.sampleRate)
        recPhase, self.ts_index = timeSync.getSyncPhase(rawZigbeePacket, pd_index, 149)
        ## CFS ##
        ## === ##
        idealPhase = np.unwrap(np.angle(self.myPacket.IQ[4:153]))  # 149 points
        fit = np.polyfit(np.arange(0, 149, 1), recPhase - idealPhase, 1)
        self.freqEstimation = fit[0] * 4000000 / np.pi
        CFS = CFS_direct(self.sampleRate, 149)
        preCorrectedSignal = CFS.compensateFrequencyAndPhase(self.freqEstimation, 0.0, rawZigbeePacket)
        ## CPS ##
        ## === ##
        synchronizer = CPS(self.sampleRate)
        self.correctedSignal, phaseVector, _ = synchronizer.costasLoop(850000., preCorrectedSignal)
        ## Symbol Detector ##
        ## =============== ##
        symbolDetector = SymbolDetector(self.sampleRate)
        self.Ibits, self.Qbits = symbolDetector.detect(self.correctedSignal[self.ts_index:])
        #self.Ibits, self.Qbits = symbolDetector.detect(rawZigbeePacket[self.ts_index:])
        ## Symbol Decoder ##
        ## ============== ##
        # symbolDecoder = SymbolDecoder(self.sampleRate)
        # self.payload = symbolDecoder.decode(self.Ibits, self.Qbits)
        # return self.payload
        return -1

if __name__ == "__main__":
    DEBUG = 0
    err = 0
    errCount = 0
    number_of_tests = 100
    for j in range(number_of_tests):
        err = 0
        # Zigbee packet
        sampleRate = 8
        if(DEBUG):
            zigbeePayloadNbOfBytes = 1
            freqOffset = 0.0
            phaseOffset = 0.0
            SNR = 15.
        else:
            zigbeePayloadNbOfBytes = randint(5,127)
            freqOffset = 0.0#float(randint(-200000,200000))
            phaseOffset = 0.0#float(randint(0,360))
            SNR = 150.
        leadingNoiseSamples = randint(1,20) * 50
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

        ## Receiver
        receiver = ZigbeeReceiver(sampleRate)
        payload = receiver.receive(receivedSignal)

        symbolDecoder = SymbolDecoder(sampleRate)
        idealIQbytes = symbolDecoder._mapToBytes(symbolDecoder._mapToSymbols(symbolDecoder._groupIn32(myPacket.messageInChip)))

        ind = (receiver.ts_index - leadingNoiseSamples) / 8

        idealIbits = [int(x) for x in myPacket.messageI[ind:]]
        idealQbits = [int(x) for x in myPacket.messageQ[ind:]]
        # compare results
        print "TEST", j+1, "PACKET SIZE =", zigbeePayloadNbOfBytes,
        if (idealIbits == receiver.Ibits or idealQbits == receiver.Ibits):
            print " OK"
        else:
            print " ERROR"
            print idealIbits
            print receiver.Ibits
            err = 1
            errCount += 1

        if(DEBUG or err):
            print idealIQbytes[:]
            print payload
            plt.subplot(2,1,1)
            plt.plot(receivedSignal.real[:receiver.ts_index+132], 'b')
            plt.axvline(x=receiver.ts_index, linewidth=2, color='k')
            plt.subplot(2,1,2)
            plt.plot(receivedSignal.real[receiver.ts_index:receiver.ts_index+129], '-xb')
            plt.plot(receiver.correctedSignal.real[receiver.ts_index:receiver.ts_index + 129], '-xk')
            plt.show()
            plt.subplot(2, 1, 1)
            plt.plot(receivedSignal.imag[:receiver.ts_index + 132], 'r')
            plt.axvline(x=receiver.ts_index, linewidth=2, color='k')
            plt.subplot(2, 1, 2)
            plt.plot(receivedSignal.imag[receiver.ts_index:receiver.ts_index + 129], '-xr')
            plt.plot(receiver.correctedSignal.imag[receiver.ts_index+4*128:receiver.ts_index + 129+4*128], '-xk')
            plt.show()

    print "============================="
    print "TOTAL ERRORS = ", errCount, "/", number_of_tests