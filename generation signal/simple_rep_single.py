#
# **************************************************************************
#
# test_repetition_4channels.py                                     (c) Spectrum GmbH
#
# **************************************************************************
#
# Example for all SpcMDrv based analog replay cards. 
# Shows a simple standard mode example using only the few necessary commands
#
# Information about the different products and their drivers can be found
# online in the Knowledge Base:
# https://www.spectrum-instrumentation.com/en/platform-driver-and-series-differences
#
# Feel free to use this source for own projects and modify it in any kind
#
# Documentation for the API as well as a detailed description of the hardware
# can be found in the manual for each device which can be found on our website:
# https://www.spectrum-instrumentation.com/en/downloads
#
# Further information can be found online in the Knowledge Base:
# https://www.spectrum-instrumentation.com/en/knowledge-base-overview
#
# **************************************************************************
#
import numpy as np

def sinus(buffer, size):
    taille_buffer = size
    freq_signal = 50e6  # Hz
    valeur_magique = 1.6 #facteur de correction car l'echantillonnage se fait a 625MS/s mais on veut une meilleure précision
    freq_signal = valeur_magique * freq_signal
    periode = 1 / freq_signal  # s
    amplitude_max = 32768
    freq_ech = 1e9  # Hz
    dt = 1 / freq_ech  # s
    phase = 0  # radians
    print(f"pas de temps: {dt}, echantillonnage: {round((1 / dt)) / 1e9}")
    temps = np.array([i * dt for i in range(taille_buffer)])
    sinus = np.sin(2 * np.pi * freq_signal * temps + phase)
    sinusd = amplitude_max * sinus
    from itertools import chain
    buffer_order = [x for x in chain.from_iterable([[x] * 4 for x in sinusd])]
    for i, x in enumerate(buffer_order):
        buffer[i] = int(x)

from pyspcm import *
from spcm_tools import *
import sys
LEVEL = 2000 #mV
#
# **************************************************************************
# main 
# **************************************************************************
#

# open card
# uncomment the second line and replace the IP address to use remote
# cards like in a generatorNETBOX
#hCard = spcm_hOpen (create_string_buffer (b'/dev/spcm0'))
hCard = spcm_hOpen (create_string_buffer (b'TCPIP::169.254.114.9::inst0::INSTR'))
if hCard == None:
    sys.stdout.write("no card found...\n")
    exit ()


# read type, function and sn and check for D/A card
lCardType = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_PCITYP, byref (lCardType))
lSerialNumber = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_PCISERIALNO, byref (lSerialNumber))
lFncType = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_FNCTYPE, byref (lFncType))

sCardName = szTypeToName (lCardType.value)
print(f"type de carte: {lFncType.value}")
if lFncType.value == SPCM_TYPE_AO:
    sys.stdout.write("Found: {0} sn {1:05d}\n".format(sCardName,lSerialNumber.value))
else:
    sys.stdout.write("This is an example for D/A cards.\nCard: {0} sn {1:05d} not supported by example\n".format(sCardName,lSerialNumber.value))
    exit ()


# set samplerate according to the type of card
if ((lCardType.value & TYP_SERIESMASK) == TYP_M4IEXPSERIES) or ((lCardType.value & TYP_SERIESMASK) == TYP_M4XEXPSERIES):
    #notre cas
    spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, MEGA(625))
else:
    spcm_dwSetParam_i64 (hCard, SPC_SAMPLERATE, MEGA(1))
spcm_dwSetParam_i32 (hCard, SPC_CLOCKOUT,   0)

# setup the mode
qwChEnable = CHANNEL0|CHANNEL1|CHANNEL2|CHANNEL3 #selection des channels actifs
llMemSamples = int64 (KILO_B(64))
llLoops = int64 (0) # loop continuously
spcm_dwSetParam_i32 (hCard, SPC_CARDMODE,    SPC_REP_STD_CONTINUOUS)
spcm_dwSetParam_i64 (hCard, SPC_CHENABLE,    qwChEnable)
spcm_dwSetParam_i64 (hCard, SPC_MEMSIZE,     llMemSamples)
spcm_dwSetParam_i64 (hCard, SPC_LOOPS,       llLoops)
#controle du fonctionnement des canaux
spcm_dwSetParam_i64 (hCard, SPC_ENABLEOUT0,  1)
spcm_dwSetParam_i64 (hCard, SPC_ENABLEOUT1,  1)
spcm_dwSetParam_i64 (hCard, SPC_ENABLEOUT2,  1)
spcm_dwSetParam_i64 (hCard, SPC_ENABLEOUT3,  1)
#filtres sur les sorties
spcm_dwSetParam_i64 (hCard, SPC_FILTER0,     1)
spcm_dwSetParam_i64 (hCard, SPC_FILTER1,     1)
spcm_dwSetParam_i64 (hCard, SPC_FILTER2,     1)
spcm_dwSetParam_i64 (hCard, SPC_FILTER3,     1)

lSetChannels = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_CHCOUNT,     byref (lSetChannels))
print(f"cannaux initialisés: {lSetChannels.value}")
lBytesPerSample = int32 (0)
spcm_dwGetParam_i32 (hCard, SPC_MIINST_BYTESPERSAMPLE,  byref (lBytesPerSample))
print(f"octets par echantillon: {lBytesPerSample.value}")
# setup the trigger mode
# (SW trigger, no output)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_ORMASK,      SPC_TMASK_SOFTWARE)
value = 0
spcm_dwSetParam_i32 (hCard, SPC_TRIG_ANDMASK,     value)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_CH_ORMASK0,  value)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_CH_ORMASK1,  value)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_CH_ANDMASK0, value)
spcm_dwSetParam_i32 (hCard, SPC_TRIG_CH_ANDMASK1, value)
spcm_dwSetParam_i32 (hCard, SPC_TRIGGEROUT,       value)

lChannel = int32 (1)
# spcm_dwSetParam_i32 (hCard, SPC_AMP0 + lChannel.value * (SPC_AMP1 - SPC_AMP0), int32 (LEVEL))
spcm_dwSetParam_i32 (hCard, SPC_AMP0, int32 (LEVEL))
spcm_dwSetParam_i32 (hCard, SPC_AMP1, int32 (LEVEL))
spcm_dwSetParam_i32 (hCard, SPC_AMP2, int32 (LEVEL))
spcm_dwSetParam_i32 (hCard, SPC_AMP3, int32 (LEVEL))
# setup software buffer
qwBufferSize = uint64 (llMemSamples.value * lBytesPerSample.value * lSetChannels.value)
print(f"nombre d'échantillons: {llMemSamples.value}\nnombre d'octets par échantillon: {lBytesPerSample.value} nombre de cannaux ouverts: {lSetChannels.value}\nqwBufferSize: {qwBufferSize.value}")

# we try to use continuous memory if available and big enough
pvBuffer = c_void_p ()
qwContBufLen = uint64 (0)
spcm_dwGetContBuf_i64 (hCard, SPCM_BUF_DATA, byref(pvBuffer), byref(qwContBufLen))
sys.stdout.write ("ContBuf length: {0:d}\n".format(qwContBufLen.value))
if qwContBufLen.value >= qwBufferSize.value:
    sys.stdout.write("Using continuous buffer\n")
else:
    pvBuffer = pvAllocMemPageAligned (qwBufferSize.value)
    sys.stdout.write("Using buffer allocated by user program\n")

# calculate the data
pnBuffer = cast  (pvBuffer, ptr16)
# for i in range (0, llMemSamples.value, 1):
#    pnBuffer[i] = i
#    print(i)

#definition du signal
sinus(pnBuffer, llMemSamples.value)

# we define the buffer for transfer and start the DMA transfer
sys.stdout.write("Starting the DMA transfer and waiting until data is in board memory\n")
spcm_dwDefTransfer_i64 (hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32 (0), pvBuffer, uint64 (0), qwBufferSize)
spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
sys.stdout.write("... data has been transferred to board memory\n")

# We'll start and wait until the card has finished or until a timeout occurs
spcm_dwSetParam_i32 (hCard, SPC_TIMEOUT, 10000)
sys.stdout.write("\nStarting the card and waiting for ready interrupt\n(continuous and single restart will have timeout)\n")

dwError = spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITREADY)


if dwError == ERR_TIMEOUT:
    spcm_dwSetParam_i32 (hCard, SPC_M2CMD, M2CMD_CARD_STOP)

spcm_vClose (hCard);

