# ZigBeePacket Class creates IEEE 802.15.4 compliant waveforms. The O-QPSK modulated signal varies in amplitude from -1
# to +1.
#
# INPUTS:
#  - payloadNbOfBytes : size of payload in bytes, from 0 to 127. payload value generated randomly
#  - sampleRate       : sample rate in MHz of the waveform. Suggested value = 8 MHz (8 samples per half-sine)
#
# OUTPUT:
#  - IQ : complex vector with In-phase (real part) and Quadrature (imaginary part) components

from System_blocks.ZigBeePacket import ZigBeePacket
from System_blocks.WirelessChannel import WirelessChannel
from System_blocks.TimeSync import TimeSynchronizer
from System_blocks.CFS_direct import CFS_direct
from System_blocks.CPS import CPS
from System_blocks.SymbolDetector import SymbolDetector

import utils
import numpy as np
import matplotlib.pyplot as plt
from random import randint


chip2Symbol = {
    "11011001110000110101001000101110" : "0000",
    "00100110001111001010110111010001" : "0000",
    "10110011100101101111010001001000" : "0000",
    "01001100011010010000101110110111" : "0000",

    "11101101100111000011010100100010" : "0001",
    "00010010011000111100101011011101" : "0001",
    "10001011001110010110111101000100" : "0001",
    "01110100110001101001000010111011" : "0001",

    "00101110110110011100001101010010" : "0010",
    "11010001001001100011110010101101" : "0010",
    "01001000101100111001011011110100" : "0010",
    "10110111010011000110100100001011" : "0010",

    "00100010111011011001110000110101" : "0011",
    "11011101000100100110001111001010" : "0011",
    "01000100100010110011100101101111" : "0011",
    "10111011011101001100011010010000" : "0011",

    "01010010001011101101100111000011" : "0100",
    "10101101110100010010011000111100" : "0100",
    "11110100010010001011001110010110" : "0100",
    "00001011101101110100110001101001" : "0100",

    "00110101001000101110110110011100" : "0101",
    "11001010110111010001001001100011" : "0101",
    "01101111010001001000101100111001" : "0101",
    "10010000101110110111010011000110" : "0101",

    "11000011010100100010111011011001" : "0110",
    "00111100101011011101000100100110" : "0110",
    "10010110111101000100100010110011" : "0110",
    "01101001000010111011011101001100" : "0110",

    "10011100001101010010001011101101" : "0111",
    "01100011110010101101110100010010" : "0111",
    "00111001011011110100010010001011" : "0111",
    "11000110100100001011101101110100" : "0111",

    "10001100100101100000011101111011" : "1000",
    "01110011011010011111100010000100" : "1000",
    "00011001001111000101111011100010" : "1000",
    "11100110110000111010000100011101" : "1000",

    "10111000110010010110000001110111" : "1001",
    "01000111001101101001111110001000" : "1001",
    "00100001100100111100010111101110" : "1001",
    "11011110011011000011101000010001" : "1001",

    "01111011100011001001011000000111" : "1010",
    "10000100011100110110100111111000" : "1010",
    "11100010000110010011110001011110" : "1010",
    "00011101111001101100001110100001" : "1010",

    "01110111101110001100100101100000" : "1011",
    "10001000010001110011011010011111" : "1011",
    "11101110001000011001001111000101" : "1011",
    "00010001110111100110110000111010" : "1011",

    "00000111011110111000110010010110" : "1100",
    "11111000100001000111001101101001" : "1100",
    "01011110111000100001100100111100" : "1100",
    "10100001000111011110011011000011" : "1100",

    "01100000011101111011100011001001" : "1101",
    "10011111100010000100011100110110" : "1101",
    "11000101111011100010000110010011" : "1101",
    "00111010000100011101111001101100" : "1101",

    "10010110000001110111101110001100" : "1110",
    "01101001111110001000010001110011" : "1110",
    "00111100010111101110001000011001" : "1110",
    "11000011101000010001110111100110" : "1110",

    "11001001011000000111011110111000" : "1111",
    "00110110100111111000100001000111" : "1111",
    "10010011110001011110111000100001" : "1111",
    "01101100001110100001000111011110" : "1111"
} # formatted in MSB first

class SymbolDecoder:
    def __init__(self, sampleRate):
        pass

    
    def _mapToBytes(self,symbolsList):
        result = []
        for i in range(len(symbolsList) / 2):
            temp = symbolsList[2 * i:2 * i + 2]
            temp = "".join([str(j) for j in temp])
            result.append(temp)
        print result
    def _mapToSymbols(self,chipList):
        result = [chip2Symbol[j] for j in chipList]
        return result
    def _groupIn32(self,vect):
        result = []
        for i in range(len(vect)/32):
            temp = vect[32*i:32*i+32]
            temp = "".join([str(j) for j in temp])
            result.append(temp)
        return result
    def _mergeIQ(self,I,Q):
        result = []
        for i in range(len(I)):
            result.append(I[i])
            result.append(Q[i])
        return result
    def _chipToSymbol(self,chip):
        pass




if __name__ == "__main__":
    DEBUG = 1
    errCount = 0
    number_of_tests = 1
    for j in range(number_of_tests):
        # Zigbee packet
        sampleRate = 8
        zigbeePayloadNbOfBytes = 0
        if (DEBUG):
            freqOffset = 0.0
            phaseOffset = 90.0
            SNR = 6000.
        else:
            freqOffset = 0.0  # float(randint(-200000,200000))
            phaseOffset = 0.0  # float(randint(0,360))
            SNR = 6.
        leadingNoiseSamples = 0
        trailingNoiseSamples = 0

        if (DEBUG):
            print "Zigbee payload size = " + str(zigbeePayloadNbOfBytes) + " bytes"
            print "Sample rate = " + str(sampleRate) + " MHz"
            print "Frequency offset = " + str(freqOffset / 1000) + " kHz"
            print "Phase offset = " + str(phaseOffset) + " Degrees"
            print "SNR = " + str(SNR) + " dB"
            print "\n"

        # payload in bytes, sample-rate in MHz
        myPacket = ZigBeePacket(zigbeePayloadNbOfBytes, sampleRate)

        ## CHANNEL
        # sample-rate (MHz), frequency offset (Hz), phase offset (degrees), SNR (db)
        myChannel = WirelessChannel(sampleRate, freqOffset, phaseOffset, SNR)
        receivedSignal = myChannel.receive(myPacket.IQ, leadingNoiseSamples, trailingNoiseSamples)

        ## Symbol Detector
        SDetect = SymbolDetector(sampleRate)
        I_est, Q_est = SDetect.detect(receivedSignal[:])  # take only the payload 1536:

        ## Symbol Decoder
        SDecoder = SymbolDecoder(sampleRate)
        #SDecoder._mapToBytes(SDecoder._mapToSymbols(SDecoder._groupIn32(SDecoder._mergeIQ(I_est,Q_est))))


        #print SDecoder._mapToBytes(SDecoder._mapToSymbols(SDecoder._groupIn32(myPacket.messageInChip)))

        print I_est
        print Q_est

        #print SDecoder._groupIn32(SDecoder._mergeIQ(I_est,Q_est))

        plt.plot(receivedSignal.real[:132],'r')
        plt.plot(receivedSignal.imag[:132],'b')
        plt.show()

        #start = 0
        #rang = 32
        #end = start + rang
        #
        #strr = "0000"
        #temp = myPacket.symbolToChip([strr,strr])
        #
        #I = temp[start:end][0::2]
        #Q = temp[start:end][1::2]
        #I_inv = [str(1 - int(i)) for i in temp[start:end][0::2]]
        #I_inv = "".join(I_inv)
        #Q_inv = [str(1 - int(i)) for i in temp[start:end][1::2]]
        #Q_inv = "".join(Q_inv)
        #
        #print " I = ",I
        #print "-I = ",I_inv
        #print " Q = ",Q
        #print "-Q = ",Q_inv
        #
        #IQ   = ""
        #_I_Q = ""
        #Q_I  = ""
        #_QI  = ""
        #for i in range(len(I)):
        #    IQ   += I[i]     + Q[i]
        #    _I_Q += I_inv[i] + Q_inv[i]
        #    Q_I  += Q[i]     + I_inv[i]
        #    _QI  += Q_inv[i] + I[i]
        #
        #print "\"" + IQ + "\"" + " : " + "\"" + strr + "\","
        #print "\"" + _I_Q + "\"" + " : " + "\"" + strr + "\","
        #print "\"" + Q_I + "\"" + " : " + "\"" + strr + "\","
        #print "\"" + _QI + "\"" + " : " + "\"" + strr + "\","
        #
        #print chip2Symbol["10010011110001011110111000100001"]