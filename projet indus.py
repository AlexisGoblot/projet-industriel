# -*- coding: utf-8 -*-
import tkinter

import numpy as np
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from generation_signal.netbox_api import *
from itertools import chain
from typing import List, Tuple, Dict, Callable

matplotlib.use("TkAgg")
LARGE_FONT = ("Verdana", 12)


def generer_secteur_angulaire(distance_element: float, lmbda: float) -> List[Tuple[np.array, np.array, str]]:
    """
    Renvoie les données nécessaires pour afficher le secteur angulaire dans l'application
    :param distance_element: distance inter-éléments dans le réseau (en m)
    :param lmbda: longueur distance_element'onde (en m)
    :return: List[Tuple[np.array, np.array, str]]
    """
    if lmbda / distance_element > 2:
        max_depointage = np.pi / 2
    else:
        max_depointage = np.arcsin((1 - distance_element / lmbda) / (distance_element / lmbda))  # depointage max

    n_points = 100
    maximum = 1
    rhos = [maximum for _ in range(n_points)]
    theta = np.linspace(-max_depointage + 90 * np.pi / 180, max_depointage + 90 * np.pi / 180, n_points)
    return [(theta, rhos, "blue"),
            (np.array([max_depointage + 90 * np.pi / 180, max_depointage + 90 * np.pi / 180]),
             np.array([0, maximum]),
             "red"),
            (np.array([-max_depointage + 90 * np.pi / 180, -max_depointage + 90 * np.pi / 180]),
             np.array([0, maximum]),
             "red")]


def calcul_phase_secteur_angulaire(pas_de_phase_radians: float, distance_element: float, lmbda: float) -> List[
    Tuple[np.array,
          np.array,
          str]]:
    """
    Calcule le dépointage réalisé par les paramètres sélectionnés.
    :param pas_de_phase_radians: pas de phase entre deux éléments du réseau (radians)
    :param distance_element: distance inter-éléments dans le réseau (en m)
    :param lmbda: longueur distance_element'onde (en m)
    :return: List[Tuple[np.array, np.array, str]]
    """
    phase_radians = np.arcsin(-pas_de_phase_radians / (2 * np.pi * distance_element / lmbda))
    phase_radians += np.pi / 2  # orgine en haut pas a droite
    return [(np.array([phase_radians, phase_radians]), np.array([0, 1]), "g")]


def generer_zone_visible(pas_de_phase_radians: float, distance_element: float, lmbda: float, orientation_cible_radians,
                         n_elem: int = 4, amplitudes: Tuple[int] = (1, 1, 1, 1), n_points: int = 500) -> Dict:
    """
    Calcule les données nécessaires pour l'affichage de la zone visible
    :param pas_de_phase_radians: pas de phase entre deux éléments du réseau (radians)
    :param distance_element: distance inter-éléments dans le réseau (en m)
    :param lmbda: longueur distance_element'onde (en m)
    :param orientation_cible_radians: orientation par rapport au réseau (radians)
    :param n_elem: nombre distance_element'éléments constituant le réseau
    :param amplitudes: les amplitudes associées aux éléments du réseau
    :param n_points: points de traçage.
    :return:
    """
    theta = np.linspace(- np.pi / 2, np.pi / 2, n_points)
    psi = pas_de_phase_radians + (2 * np.pi / lmbda) * distance_element * np.sin(theta)
    af = calculer_facteur_reseau(psi, n_elem, amplitudes)
    ylim = sum(amplitudes)
    x1, x2 = borne_zone_visible(pas_de_phase_radians, distance_element, lmbda)
    return {
        "max": ylim,
        "data": [
            (np.array([x1, x1]), np.array([0, -40]), "red"),
            (np.array([x2, x2]), np.array([0, -40]), "red"),
            (psi, af, "blue"),
            (np.array([pas_de_phase_radians, pas_de_phase_radians]), np.array([0, -40]), "green"),
            (np.array([orientation_cible_radians, orientation_cible_radians]), np.array([0, -40]), "orange")]
    }


def borne_zone_visible(pas_de_phase_radians: float, distance_element: float, lmbda: float) -> Tuple[float, float]:
    """
    Calcule les bornes du domaine visible en fonction des paramètres sélectionnées.
    :param pas_de_phase_radians: pas de phase entre deux éléments du réseau (radians)
    :param distance_element: distance inter-éléments dans le réseau (en m)
    :param lmbda: longueur distance_element'onde (en m)
    :return: Tuple[float, float]
    """
    return (pas_de_phase_radians - 2 * np.pi * distance_element / lmbda,
            pas_de_phase_radians + 2 * np.pi * distance_element / lmbda)


def calcul_sinus_analogique(freq_signal, amplitude, phase_radians, facteur_correction, taille_buffer=65536):
    freq_ech = 1e9  # Hz
    dt = 1 / freq_ech  # s

    freq_signal = facteur_correction * freq_signal
    print(f"freq signal corrigé:{freq_signal}")
    print(f"pas de temps: {dt}, periode:{1 / freq_signal}")

    # échelle des temps
    temps = np.array([i * dt for i in range(taille_buffer)])

    # signaux normalisés a 1
    sinus = amplitude * np.sin(2 * np.pi * freq_signal * temps + phase_radians)
    return temps, sinus


def calculer_facteur_reseau(psi: np.array, n_elem: int = 4, amplitudes: Tuple[int] = (1, 1, 1, 1)) \
        -> np.array:
    """
    Calcule le module du facteur de réseau en fonction de psi, du nombre d'éléments dans le réseau, ainsi que des
    amplitudes associées aux éléments du réseau.
    :param psi: angles (radians).
    :param n_elem: nombre d'éléments constituant le réseau.
    :param amplitudes: liste d'amplitudes correspondant aux éléments du réseau.
    :return: np.array
    """
    af = amplitudes[0] * np.exp(0 * 1j * psi)
    for i in range(1, n_elem):
        af += amplitudes[i] * np.exp(i * 1j * psi)
    return np.abs(af)


def maj_stringvar(stringvar1: tkinter.StringVar, stringvar2: tkinter.StringVar, fonction: Callable) -> None:
    """
    Utilisé par la stringvar de la longueur d'onde pour etre maj automatiquement en fonction de la fréquence.
    """
    stringvar2.set(fonction(stringvar1.get()))


class MainFrame(tk.Frame):
    """
    Classe qui contient tous les éléments graphiques de l'application.
    """

    def __init__(self, main_window: tk.Tk) -> None:
        """
        Constructeur de la classe. Instancie tous les éléments graphiques.
        :type main_window: tk.Tk
        Fenêtre principale de tkinter
        """
        tk.Frame.__init__(self, main_window)
        self.main = main_window

        # labels
        self.label_distance_elements = tk.Label(self.main, text="distance inter-éléments (m)")
        self.label_frequence = tk.Label(self.main, text="fréquence (GHz)")
        self.label_longueur_onde = tk.Label(self.main, text="longueur d'onde (m)")
        self.label_pas_de_phase = tk.Label(self.main, text="pas de déphasage (degrés)")
        self.label_frequence_rf = tk.Label(self.main, text="fréquence RF (MHz)")

        self.label_phase_1 = tk.Label(self.main, text="phase voie 1 (°):")
        self.label_phase_2 = tk.Label(self.main, text="phase voie 2 (°):")
        self.label_phase_3 = tk.Label(self.main, text="phase voie 3 (°):")
        self.label_phase_4 = tk.Label(self.main, text="phase voie 4 (°):")

        self.label_amplitude_1 = tk.Label(self.main, text="amplitude voie 1 (mV):")
        self.label_amplitude_2 = tk.Label(self.main, text="amplitude voie 2 (mV):")
        self.label_amplitude_3 = tk.Label(self.main, text="amplitude voie 3 (mV):")
        self.label_amplitude_4 = tk.Label(self.main, text="amplitude voie 4 (mV):")

        self.label_ponderation_1 = tk.Label(self.main, text="pondération voie 1(0-1):")
        self.label_ponderation_2 = tk.Label(self.main, text="pondération voie 2(0-1):")
        self.label_ponderation_3 = tk.Label(self.main, text="pondération voie 3(0-1):")
        self.label_ponderation_4 = tk.Label(self.main, text="pondération voie 4(0-1):")

        self.label_filtres_netbox = tk.Label(self.main, text="filtres netbox")
        self.label_orientation_cible = tk.Label(self.main, text="orientation cible (°)")

        # stringvar
        self.stringvar_distance_element = tk.StringVar(value="0.11")
        self.stringvar_frequence = tk.StringVar(value="3.5")
        self.stringvar_frequence.trace("w",
                                       lambda name, index, mode, sv=self.stringvar_frequence:
                                       maj_stringvar(sv,
                                                     self.stringvar_longeur_onde,
                                                     lambda x: 3e8 / (float(x) * 1e9)))

        self.stringvar_longeur_onde = tk.StringVar(value=str(3e8 / 3.5e9))
        self.stringvar_pas_de_phase = tk.StringVar(value="0")
        self.stringvar_pas_de_phase.trace("w",
                                          lambda name, index, mode, sv=self.stringvar_pas_de_phase:
                                          (maj_stringvar(sv, self.stringvar_phase_1, lambda x: 0),
                                           maj_stringvar(sv, self.stringvar_phase_2, lambda x: float(x) % 360),
                                           maj_stringvar(sv, self.stringvar_phase_3, lambda x: 2 * float(x) % 360),
                                           maj_stringvar(sv, self.stringvar_phase_4, lambda x: 3 * float(x) % 360)))

        self.stringvar_phase_1 = tk.StringVar(value="0")
        self.stringvar_phase_2 = tk.StringVar(value="0")
        self.stringvar_phase_3 = tk.StringVar(value="0")
        self.stringvar_phase_4 = tk.StringVar(value="0")

        self.stringvar_amplitude_1 = tk.StringVar(value="2000")
        self.stringvar_amplitude_2 = tk.StringVar(value="2000")
        self.stringvar_amplitude_3 = tk.StringVar(value="2000")
        self.stringvar_amplitude_4 = tk.StringVar(value="2000")

        self.stringvar_ponderation_1 = tk.StringVar(value="1")
        self.stringvar_ponderation_2 = tk.StringVar(value="1")
        self.stringvar_ponderation_3 = tk.StringVar(value="1")
        self.stringvar_ponderation_4 = tk.StringVar(value="1")

        self.stringvar_frequence_rf = tk.StringVar(value="75")
        self.stringvar_filtres_netbox = tk.StringVar(value="1")
        self.stringvar_orientation_cible = tk.StringVar(value="0")

        # button
        self.bouton_validation = tk.Button(self.main, text="valider", command=self.maj_figures)
        self.bouton_generation_signal = tk.Button(self.main, text="générer signaux", command=self.start_signaux)
        self.bouton_stop_signal = tk.Button(self.main, text="stopper signaux", command=self.stop_signaux)

        #boutons radio
        self.bouton_radio_sans_filtre = tk.Radiobutton(self.main, variable=self.stringvar_filtres_netbox, text="sans filtre", value="0")
        self.bouton_radio_filtre_65_mhz = tk.Radiobutton(self.main, variable=self.stringvar_filtres_netbox, text="filtre 65MHz", value="1")
        self.bouton_radio_filtre_65_mhz.select()

        # entry
        self.entry_distance_element = tk.Entry(self.main, textvariable=self.stringvar_distance_element)
        self.entry_frequence = tk.Entry(self.main, textvariable=self.stringvar_frequence)
        self.entry_longeur_onde = tk.Entry(self.main, textvariable=self.stringvar_longeur_onde)
        self.entry_pas_de_phase = tk.Entry(self.main, textvariable=self.stringvar_pas_de_phase)

        self.entry_phase_1 = tk.Entry(self.main, textvariable=self.stringvar_phase_1, width=5)
        self.entry_phase_2 = tk.Entry(self.main, textvariable=self.stringvar_phase_2, width=5)
        self.entry_phase_3 = tk.Entry(self.main, textvariable=self.stringvar_phase_3, width=5)
        self.entry_phase_4 = tk.Entry(self.main, textvariable=self.stringvar_phase_4, width=5)

        self.entry_amplitude_1 = tk.Entry(self.main, textvariable=self.stringvar_amplitude_1, width=5)
        self.entry_amplitude_2 = tk.Entry(self.main, textvariable=self.stringvar_amplitude_2, width=5)
        self.entry_amplitude_3 = tk.Entry(self.main, textvariable=self.stringvar_amplitude_3, width=5)
        self.entry_amplitude_4 = tk.Entry(self.main, textvariable=self.stringvar_amplitude_4, width=5)

        self.entry_ponderation_1 = tk.Entry(self.main, textvariable=self.stringvar_ponderation_1, width=5)
        self.entry_ponderation_2 = tk.Entry(self.main, textvariable=self.stringvar_ponderation_2, width=5)
        self.entry_ponderation_3 = tk.Entry(self.main, textvariable=self.stringvar_ponderation_3, width=5)
        self.entry_ponderation_4 = tk.Entry(self.main, textvariable=self.stringvar_ponderation_4, width=5)

        self.entry_frequence_rf = tk.Entry(self.main, textvariable=self.stringvar_frequence_rf, width=5)
        self.entry_orientation_cible = tk.Entry(self.main, textvariable=self.stringvar_orientation_cible, width=5)

        # figures
        self.figure_secteur_angulaire = Figure()
        self.figure_zone_visible = Figure()
        self.figure_signaux_generes = Figure()

        # canvas
        self.canvas_secteur_angulaire = FigureCanvasTkAgg(self.figure_secteur_angulaire, master=self.main)
        self.canvas_zone_visible = FigureCanvasTkAgg(self.figure_zone_visible, master=self.main)
        self.canvas_signaux_generes = FigureCanvasTkAgg(self.figure_signaux_generes, master=self.main)

        # init visual
        self.initialisation_widgets()

    def initialisation_figure_angulaire(self) -> None:
        """
        Permet distance_element'initialiser la figure angulaire de l'application.
        :return: None
        """
        axe = self.figure_secteur_angulaire.gca(polar=True)
        axe.clear()
        maximum = 1
        minimum = 0
        nb_lines = 5
        axe.set_rticks(np.linspace(minimum, maximum, nb_lines))  # grille radiale
        axe.set_xticks(np.linspace(0, np.pi, 13))
        axe.set_xticklabels([f"{format(-((x * 180 / np.pi) - 90), '.2f')}°" for x in np.linspace(0, np.pi, 13)])
        axe.set_ylim(bottom=minimum, top=maximum, auto=False)  # gestion des limites radiale
        axe.set_xlim(left=np.pi, right=0, auto=False)  # gestion des limites angulaires
        axe.set_rlabel_position(-22.5)
        axe.set_yticklabels([])
        # axe.title("dépointage")

    def maj_figure_angulaire(self, pas_de_phase_radians: float, distance_element: float, lmbda: float) -> None:
        """
        Mets à jour la figure angulaire avec les paramètres souhaités.
        :param pas_de_phase_radians: pas de phase (en radians) souhaité entre les différents éléments du réseau.
        :param distance_element: distance inter-éléments du réseau (en m)
        :param lmbda: la longueur distance_element'onde (en m)
        :return: None
        """
        self.initialisation_figure_angulaire()
        axe = self.figure_secteur_angulaire.gca(polar=True)
        for x, y, color in generer_secteur_angulaire(distance_element, lmbda) + calcul_phase_secteur_angulaire(
                pas_de_phase_radians, distance_element,
                lmbda):
            axe.plot(x, y, color=color)
        axe.set_title("dépointage")

        self.canvas_secteur_angulaire.draw()

    def initialisation_figure_zone_visible(self) -> None:
        """
        Initialise la figure pour la zone visible.
        :return: None
        """
        plotter = self.figure_zone_visible.gca()
        plotter.clear()
        plotter.set_xlabel("psi (degrés)")
        plotter.set_ylabel("AF")
        plotter.set_title("zone visible")

    def maj_figure_zone_visible(self, pas_de_phase_radians: float, distance_element: float, lmbda: float) -> None:
        """
        Met à jour la figure pour la zone visible avec les paramètres souhaités.
        :param pas_de_phase_radians: pas de phase (en radians) souhaité entre les différents éléments du réseau.
        :param distance_element: distance inter-éléments du réseau (en m)
        :param lmbda: la longueur distance_element'onde (en m)
        :return: None
        """
        self.initialisation_figure_zone_visible()
        amplitudes = (float(self.stringvar_ponderation_1.get()),
                      float(self.stringvar_ponderation_2.get()),
                      float(self.stringvar_ponderation_3.get()),
                      float(self.stringvar_ponderation_4.get()),
                      )
        orientation_cible_radians = float(self.stringvar_orientation_cible.get())*np.pi/180
        orientation_cible_radians = np.sin(orientation_cible_radians)*2*np.pi*distance_element/lmbda + pas_de_phase_radians
        data = generer_zone_visible(pas_de_phase_radians, distance_element, lmbda, orientation_cible_radians, amplitudes=amplitudes)
        axe = self.figure_zone_visible.gca()

        # reprocessing data
        borne_inf, borne_sup, courbe, origine, orientation_cible = data["data"]
        courbe = list(courbe)
        courbe[1] = 10 * np.log(courbe[1] / data["max"])
        courbe = tuple(courbe)

        # zoom
        axe.set_ylim(-40, 0)
        # axe.set_xlim(borne_inf[0][0]*180/np.pi, borne_sup[0][0]*180/np.pi)

        for x, y, color in [borne_inf, borne_sup, courbe, origine, orientation_cible]:
            axe.plot(x * 180 / np.pi, y, color=color)
        self.canvas_zone_visible.draw()

    def initialisation_figure_signaux_generes(self) -> None:
        """
        Initialise la figure pour les signaux générés.
        :return: None
        """
        axes = self.figure_signaux_generes.gca()
        axes.clear()
        axes.set_xlabel("temps(s)")
        axes.set_ylabel("signaux numériques")
        axes.set_title("signaux générés numériquement")

    def obtention_sinus_analogique(self, freq_ech_netbox=625e6, freq_ech=1000e6):
        params = ((0, float(self.stringvar_ponderation_1.get()), float(self.stringvar_phase_1.get())),
                  (1, float(self.stringvar_ponderation_2.get()), float(self.stringvar_phase_2.get())),
                  (2, float(self.stringvar_ponderation_3.get()), float(self.stringvar_phase_3.get())),
                  (3, float(self.stringvar_ponderation_4.get()), float(self.stringvar_phase_4.get())))

        freq_rf = int(float(self.stringvar_frequence_rf.get()) * 1e6)

        # facteur de correction car l'echantillonnage se fait a 625MS/s mais on veut une meilleure précision
        facteur_correction = freq_ech / freq_ech_netbox
        periode = 1 / (freq_rf * facteur_correction)
        courbes = []
        for i, ponderation, phase in params:
            temps, signal = calcul_sinus_analogique(freq_rf, ponderation, phase * np.pi / 180, facteur_correction)
            courbes.append(signal)
        return tuple([temps] + courbes + [periode])

    def maj_signaux_generes(self, *args, **kwargs) -> None:
        self.initialisation_figure_signaux_generes()
        data = self.obtention_sinus_analogique()
        temps = data[0]
        signaux = data[1:-1]
        periode = data[-1]
        axe = self.figure_signaux_generes.gca()
        for i, signal in enumerate(signaux):
            axe.plot(temps, signal, label=f"voie {i + 1}")
        axe.set_xlim(0, periode)
        axe.legend()

        self.canvas_signaux_generes.draw()

    def maj_figures(self) -> None:
        """
        Méthode appelée lorsque le bouton de validation est pressé. Mets à jour les deux figures.
        :return: None
        """
        distance_element = float(self.stringvar_distance_element.get())
        lmbda = float(self.stringvar_longeur_onde.get())
        pas_de_phase_radians = float(self.stringvar_pas_de_phase.get()) * np.pi / 180

        self.maj_figure_angulaire(pas_de_phase_radians, distance_element, lmbda)
        self.maj_figure_zone_visible(pas_de_phase_radians, distance_element, lmbda)
        self.maj_signaux_generes()

    def initialisation_widgets(self) -> None:
        """
        Initialise l'affichage tous les widgets de l'application.
        :return: None
        """
        self.label_distance_elements.grid(row=0, column=0, sticky="wens")
        self.entry_distance_element.grid(row=1, column=0, sticky="wens")
        self.label_frequence.grid(row=2, column=0, sticky="wens")
        self.entry_frequence.grid(row=3, column=0, sticky="wens")
        self.label_longueur_onde.grid(row=4, column=0, sticky="wens")
        self.entry_longeur_onde.grid(row=5, column=0, sticky="wens")
        self.label_pas_de_phase.grid(row=6, column=0, sticky="wens")

        #gros bloc de commandes
        index_debut_bloc_ligne = 8
        self.label_phase_1.grid(row=index_debut_bloc_ligne , column=1, sticky="wens")
        self.entry_phase_1.grid(row=index_debut_bloc_ligne , column=2, sticky="wens")
        self.label_phase_2.grid(row=index_debut_bloc_ligne , column=3, sticky="wens")
        self.entry_phase_2.grid(row=index_debut_bloc_ligne , column=4, sticky="wens")
        self.label_phase_3.grid(row=index_debut_bloc_ligne , column=5, sticky="wens")
        self.entry_phase_3.grid(row=index_debut_bloc_ligne , column=6, sticky="wens")
        self.label_phase_4.grid(row=index_debut_bloc_ligne , column=7, sticky="wens")
        self.entry_phase_4.grid(row=index_debut_bloc_ligne , column=8, sticky="wens")

        # self.label_amplitude_1.grid(row=index_debut_bloc_ligne + 1, column=1)
        # self.entry_amplitude_1.grid(row=index_debut_bloc_ligne + 1, column=2)
        # self.label_amplitude_2.grid(row=index_debut_bloc_ligne + 1, column=3)
        # self.entry_amplitude_2.grid(row=index_debut_bloc_ligne + 1, column=4)
        # self.label_amplitude_3.grid(row=index_debut_bloc_ligne + 1, column=5)
        # self.entry_amplitude_3.grid(row=index_debut_bloc_ligne + 1, column=6)
        # self.label_amplitude_4.grid(row=index_debut_bloc_ligne + 1, column=7)
        # self.entry_amplitude_4.grid(row=index_debut_bloc_ligne + 1, column=8)

        self.label_ponderation_1.grid(row=index_debut_bloc_ligne + 1, column=1, sticky="wens")
        self.entry_ponderation_1.grid(row=index_debut_bloc_ligne + 1, column=2, sticky="wens")
        self.label_ponderation_2.grid(row=index_debut_bloc_ligne + 1, column=3, sticky="wens")
        self.entry_ponderation_2.grid(row=index_debut_bloc_ligne + 1, column=4, sticky="wens")
        self.label_ponderation_3.grid(row=index_debut_bloc_ligne + 1, column=5, sticky="wens")
        self.entry_ponderation_3.grid(row=index_debut_bloc_ligne + 1, column=6, sticky="wens")
        self.label_ponderation_4.grid(row=index_debut_bloc_ligne + 1, column=7, sticky="wens")
        self.entry_ponderation_4.grid(row=index_debut_bloc_ligne + 1, column=8, sticky="wens")

        self.label_orientation_cible.grid(row=index_debut_bloc_ligne + 2, column=1, sticky="wens")
        self.entry_orientation_cible.grid(row=index_debut_bloc_ligne + 2, column=2, sticky="wens")

        self.label_filtres_netbox.grid(row=index_debut_bloc_ligne + 3, column=1, sticky="wens")
        self.bouton_radio_sans_filtre.grid(row=index_debut_bloc_ligne + 3, column=2, sticky="wens")
        self.bouton_radio_filtre_65_mhz.grid(row=index_debut_bloc_ligne + 3, column=3, sticky="wens")

        self.entry_pas_de_phase.grid(row=7, column=0, sticky="wens")
        self.label_frequence_rf.grid(row=8, column=0, sticky="wens")
        self.entry_frequence_rf.grid(row=9, column=0, sticky="wens")
        self.bouton_validation.grid(row=10, column=0, sticky="wens")
        self.bouton_generation_signal.grid(row=11, column=0, sticky="wens")
        self.bouton_stop_signal.grid(row=12, column=0, sticky="wens")
        self.canvas_zone_visible.get_tk_widget().grid(row=13, column=0, columnspan=5, sticky="wens")
        self.canvas_secteur_angulaire.get_tk_widget().grid(row=13, column=4, columnspan=5, sticky="wens")
        self.canvas_signaux_generes.get_tk_widget().grid(row=13, column=9, columnspan=5, sticky="wens")

    def process_buffer(self, pv_buffer):
        pn_buffer = cast(pv_buffer, ptr16)
        data = self.obtention_sinus_analogique()
        signaux = data[1:-1]
        # digitalisation des signaux
        amplitude_max = 32768
        signaux = [[int(amplitude_max * valeur) for valeur in signal] for signal in signaux]
        valeurs_buffer = [x for x in chain.from_iterable([x for x in zip(*signaux)])]
        for i, valeur in enumerate(valeurs_buffer):
            pn_buffer[i] = valeur
        return pn_buffer

    def recuperation_niveaux(self):
        def borne_niveau(niveau):
            if niveau < 0:
                return 0
            if niveau <= 2000:
                return niveau
            return 2000

        niveau_1 = int(self.stringvar_amplitude_1.get())
        niveau_2 = int(self.stringvar_amplitude_2.get())
        niveau_3 = int(self.stringvar_amplitude_3.get())
        niveau_4 = int(self.stringvar_amplitude_4.get())

        niveaux = [niveau_1, niveau_2, niveau_3, niveau_4]
        niveaux = [borne_niveau(niveau) for niveau in niveaux]
        return niveaux

    def start_signaux(self):
        carte = ouverture_carte("169.254.114.9", 0)
        type_carte = check_card(carte)
        init_vitesse_sampling(type_carte, carte)
        taille_buffer = init_canaux(carte, filtres=bool(int(self.stringvar_filtres_netbox.get())))
        # niveaux = self.recuperation_niveaux()
        maj_amplitude(carte)
        pv_buffer = init_buffer(carte, taille_buffer)
        pn_buffer = self.process_buffer(pv_buffer)
        transfert_netbox(carte, pv_buffer, taille_buffer)
        start(carte, timeout=True, timeout_duration=10000, exit_on_timeout=True)
        print("actif")
        fermeture_carte(carte)

    def stop_signaux(self):
        carte = ouverture_carte("169.254.114.9", 0)
        stop(carte)
        fermeture_carte(carte)
        print("inactif")


if __name__ == "__main__":
    plt.rcParams["figure.figsize"] = [4, 4]
    main = tk.Tk()
    main_frame = MainFrame(main)
    main_frame.grid()
    main.mainloop()
# todo: basculer le gestionnaire de position sur grid au lieu de pack
# todo: commenter le code
