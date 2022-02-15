import matplotlib.pyplot as plt
import numpy as np
from scipy.fftpack import fftshift
from scipy import fft
from binconv import signe2normal

if __name__ == "__main__":
    # fe = 5e8 #Hz
    fe  =625e6
    Te = 1/fe
    n_points = 2**16 #taille du buffer
    temps = np.array([n*Te for n in range(n_points)]) # abscisse d'échantillonnage

    fs = 78e6 # Hz
    Ts = 1/fs # s
    Ws = 2*np.pi*fs # rad/s
    phi = 0 # radians
    sinus = np.sin(Ws*temps+phi)

    plt.plot(temps, sinus)
    plt.title("signal temporel généré")
    plt.xlabel("temps(s)")
    plt.ylabel("valeur du sinus")
    plt.xlim((0, 3*Ts))
    plt.show()

    n_points_fft = 2**16
    fft_sinus = fftshift(fft(sinus))
    dt = temps[1] - temps[0] #pas de temps
    df = 1 / dt # bande
    # construction de l'abscisse fréquentiel correspondant à la FFT
    freqs = np.linspace(0, df, n_points_fft) - df / 2
    plt.plot(freqs, np.abs(fft_sinus))
    plt.xlabel("frequences (Hz)")
    plt.ylabel("valeurs du module de la fft")
    plt.title("fft du signal généré")
    plt.xlim((75e6, 80e6))
    plt.show()

    amplitude_max = 2**15
    sinusd = [int(x) for x in amplitude_max * sinus + amplitude_max]

    sinusbin = [signe2normal(bin(x)) for x in sinusd]
    plt.plot(temps, sinusbin)
    plt.show()
    from itertools import chain
    test= [i for i in range(10)]
    test2= [[x]*4 for x in test]
    test3 = [x for x in chain.from_iterable(test2)]
    print(test3)


