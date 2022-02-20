from pyspcm import *
from spcm_tools import *
import sys
import numpy as np


def sinus(buffer, size):
    taille_buffer = size
    freq_signal = 50e6  # Hz
    valeur_magique = 1.6  # facteur de correction car l'echantillonnage se fait a 625MS/s mais on veut une meilleure précision
    freq_signal = valeur_magique * freq_signal
    periode = 1 / freq_signal  # s
    amplitude_max = 32768
    freq_ech = 1e9  # Hz
    dt = 1 / freq_ech  # s
    phase = 0  # radians
    print(f"pas de temps: {dt}, echantillonnage: {round((1 / dt)) / 1e9} GHz")
    temps = np.array([i * dt for i in range(taille_buffer)])
    sinus = np.sin(2 * np.pi * freq_signal * temps + phase)
    sinusd = amplitude_max * sinus
    from itertools import chain
    buffer_order = [x for x in chain.from_iterable([[x] * 4 for x in sinusd])]
    print(buffer_order[4])
    for i, x in enumerate(buffer_order):
        buffer[i] = int(x)


def ouverture_carte(ip, card_number):
    address = f'TCPIP::{ip}::inst{card_number}::INSTR'.encode()
    hcard = spcm_hOpen(create_string_buffer(address))
    if hcard is None:
        sys.stdout.write("no card found...\n")
        exit()
    return hcard


def fermeture_carte(hcard):
    spcm_vClose(hcard)


def check_card(hcard):
    # read type, function and sn and check for D/A card
    l_card_type = int32(0)
    spcm_dwGetParam_i32(hcard, SPC_PCITYP, byref(l_card_type))
    l_serial_number = int32(0)
    spcm_dwGetParam_i32(hcard, SPC_PCISERIALNO, byref(l_serial_number))
    l_fnc_type = int32(0)
    spcm_dwGetParam_i32(hcard, SPC_FNCTYPE, byref(l_fnc_type))

    s_card_name = szTypeToName(l_card_type.value)
    print(f"type de carte: {l_fnc_type.value}")
    if l_fnc_type.value == SPCM_TYPE_AO:
        sys.stdout.write("carte trouvée: {0} sn {1:05d}\n".format(s_card_name, l_serial_number.value))
        return l_card_type
    else:
        sys.stdout.write(
            "code écrit pour une carte N->A.\n" \
            "Carte: {0} sn {1:05d} n'est pas supporté\n".format(s_card_name, l_serial_number.value))
        raise TypeError("carte non supportée")


def init_vitesse_sampling(lCardType, hCard, freq_ech_netbox=625):
    if ((lCardType.value & TYP_SERIESMASK) == TYP_M4IEXPSERIES) or (
            (lCardType.value & TYP_SERIESMASK) == TYP_M4XEXPSERIES):
        # notre cas
        spcm_dwSetParam_i64(hCard, SPC_SAMPLERATE, MEGA(freq_ech_netbox))
    else:
        spcm_dwSetParam_i64(hCard, SPC_SAMPLERATE, MEGA(1))
    spcm_dwSetParam_i32(hCard, SPC_CLOCKOUT, 0)


def init_canaux(hcard, channels=CHANNEL0 | CHANNEL1 | CHANNEL2 | CHANNEL3, filtres=True):
    qwChEnable = channels  # selection des channels actifs
    llMemSamples = int64(KILO_B(64))
    llLoops = int64(0)  # loop continuously
    spcm_dwSetParam_i32(hcard, SPC_CARDMODE, SPC_REP_STD_CONTINUOUS)
    spcm_dwSetParam_i64(hcard, SPC_CHENABLE, qwChEnable)
    spcm_dwSetParam_i64(hcard, SPC_MEMSIZE, llMemSamples)
    spcm_dwSetParam_i64(hcard, SPC_LOOPS, llLoops)
    # controle du fonctionnement des canaux
    spcm_dwSetParam_i64(hcard, SPC_ENABLEOUT0, 1)
    spcm_dwSetParam_i64(hcard, SPC_ENABLEOUT1, 1)
    spcm_dwSetParam_i64(hcard, SPC_ENABLEOUT2, 1)
    spcm_dwSetParam_i64(hcard, SPC_ENABLEOUT3, 1)
    # filtres sur les sorties
    if filtres:
        spcm_dwSetParam_i64(hcard, SPC_FILTER0, 1)
        spcm_dwSetParam_i64(hcard, SPC_FILTER1, 1)
        spcm_dwSetParam_i64(hcard, SPC_FILTER2, 1)
        spcm_dwSetParam_i64(hcard, SPC_FILTER3, 1)
    else:
        spcm_dwSetParam_i64(hcard, SPC_FILTER0, 0)
        spcm_dwSetParam_i64(hcard, SPC_FILTER1, 0)
        spcm_dwSetParam_i64(hcard, SPC_FILTER2, 0)
        spcm_dwSetParam_i64(hcard, SPC_FILTER3, 0)

    lSetChannels = int32(0)
    spcm_dwGetParam_i32(hcard, SPC_CHCOUNT, byref(lSetChannels))
    lBytesPerSample = int32(0)
    spcm_dwGetParam_i32(hcard, SPC_MIINST_BYTESPERSAMPLE, byref(lBytesPerSample))

    buffSize = llMemSamples.value * lBytesPerSample.value * lSetChannels.value
    print(
        f"nombre d'échantillons: {llMemSamples.value}\nnombre d'octets par échantillon: {lBytesPerSample.value} nombre de cannaux ouverts: {lSetChannels.value}\nqwBufferSize: {buffSize}")
    return buffSize


def init_trigger(hcard):
    # setup the trigger mode
    # (SW trigger, no output)
    spcm_dwSetParam_i32(hcard, SPC_TRIG_ORMASK, SPC_TMASK_SOFTWARE)
    value = 0
    spcm_dwSetParam_i32(hcard, SPC_TRIG_ANDMASK, value)
    spcm_dwSetParam_i32(hcard, SPC_TRIG_CH_ORMASK0, value)
    spcm_dwSetParam_i32(hcard, SPC_TRIG_CH_ORMASK1, value)
    spcm_dwSetParam_i32(hcard, SPC_TRIG_CH_ANDMASK0, value)
    spcm_dwSetParam_i32(hcard, SPC_TRIG_CH_ANDMASK1, value)
    spcm_dwSetParam_i32(hcard, SPC_TRIGGEROUT, value)


def maj_amplitude(hcard, level=2000):
    spcm_dwSetParam_i32(hcard, SPC_AMP0, int32(level))
    spcm_dwSetParam_i32(hcard, SPC_AMP1, int32(level))
    spcm_dwSetParam_i32(hcard, SPC_AMP2, int32(level))
    spcm_dwSetParam_i32(hcard, SPC_AMP3, int32(level))


def init_buffer(hCard, buffSize):
    # setup software buffer
    qwBufferSize = uint64(buffSize)

    # we try to use continuous memory if available and big enough
    pvBuffer = c_void_p()
    qwContBufLen = uint64(0)
    spcm_dwGetContBuf_i64(hCard, SPCM_BUF_DATA, byref(pvBuffer), byref(qwContBufLen))
    sys.stdout.write("ContBuf length: {0:d}\n".format(qwContBufLen.value))
    if qwContBufLen.value >= qwBufferSize.value:
        sys.stdout.write("Using continuous buffer\n")
    else:
        pvBuffer = pvAllocMemPageAligned(qwBufferSize.value)
        sys.stdout.write("Using buffer allocated by user program\n")
    return pvBuffer


def calcul_signaux(pvBuffer):
    # calculate the data
    pnBuffer = cast(pvBuffer, ptr16)
    # for i in range (0, llMemSamples.value, 1):
    #    pnBuffer[i] = i
    #    print(i)

    # definition du signal
    sinus(pnBuffer, 65536)
    return pnBuffer


def transfert_netbox(hCard, pvBuffer, buffSize):
    # we define the buffer for transfer and start the DMA transfer
    sys.stdout.write("Starting the DMA transfer and waiting until data is in board memory\n")
    spcm_dwDefTransfer_i64(hCard, SPCM_BUF_DATA, SPCM_DIR_PCTOCARD, int32(0), pvBuffer, uint64(0), buffSize)
    spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_DATA_STARTDMA | M2CMD_DATA_WAITDMA)
    sys.stdout.write("... data has been transferred to board memory\n")


def stop(hCard):
    spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_STOP)


def start(hCard, timeout=True, timeout_duration=100, exit_on_timeout=False):
    if timeout:
        spcm_dwSetParam_i32(hCard, SPC_TIMEOUT, timeout_duration)
    # sys.stdout.write(
    #     "\nStarting the card and waiting for ready interrupt\n(continuous and single restart will have timeout)\n")

    # dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START | M2CMD_CARD_ENABLETRIGGER | M2CMD_CARD_WAITREADY)
    dwError = spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_START |M2CMD_CARD_ENABLETRIGGER)
    if exit_on_timeout and dwError == ERR_TIMEOUT:
        spcm_dwSetParam_i32(hCard, SPC_M2CMD, M2CMD_CARD_STOP)


if __name__ == "__main__":
    carte = ouverture_carte("169.254.114.9", 0)
    type_carte = check_card(carte)
    init_vitesse_sampling(type_carte, carte)
    taille_buffer = init_canaux(carte)
    maj_amplitude(carte)
    pvBuffer = init_buffer(carte, taille_buffer)
    pnBuffer = calcul_signaux(pvBuffer)
    transfert_netbox(carte, pvBuffer, taille_buffer)
    start(carte, timeout=True)
    fermeture_carte(carte)

#
