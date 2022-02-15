# -*- coding: utf-8 -*-
import tkinter

import numpy as np
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from generation_signal.netbox_api import *

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


def generer_zone_visible(pas_de_phase_radians: float, distance_element: float, lmbda: float, n_elem: int = 4,
                         amplitudes: Tuple[int] = (1, 1, 1, 1), n_points: int = 500) -> Dict:
    """
    Calcule les données nécessaires pour l'affichage de la zone visible
    :param pas_de_phase_radians: pas de phase entre deux éléments du réseau (radians)
    :param distance_element: distance inter-éléments dans le réseau (en m)
    :param lmbda: longueur distance_element'onde (en m)
    :param n_elem: nombre distance_element'éléments constituant le réseau
    :param amplitudes: les amplitudes associées aux éléments du réseau
    :param n_points: points de traçage.
    :return:
    """
    theta = np.linspace(-2 * np.pi, 2 * np.pi, n_points)
    psi = pas_de_phase_radians + (2 * np.pi / lmbda) * distance_element * np.sin(theta)
    af = calculer_facteur_reseau(psi, n_elem, amplitudes)
    ylim = sum(amplitudes)
    x1, x2 = borne_zone_visible(pas_de_phase_radians, distance_element, lmbda)
    print(x1, x2)
    return {
        "max": ylim,
        "data": [
            (np.array([x1, x1]), np.array([0, ylim]), "red"),
            (np.array([x2, x2]), np.array([0, ylim]), "red"),
            (psi, af, "blue"),
            (np.array([pas_de_phase_radians, pas_de_phase_radians]), np.array([0, ylim]), "green")]
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
        label = tk.Label(self, text="Déphasage signal", font=LARGE_FONT)
        label.pack(pady=10, padx=10)
        self.main = main_window

        # labels
        self.label_distance_elements = tk.Label(self.main, text="distance inter-éléments (m)")
        self.label_frequence = tk.Label(self.main, text="fréquence (GHz)")
        self.label_longueur_onde = tk.Label(self.main, text="longueur d'onde (m)")
        self.label_pas_de_phase = tk.Label(self.main, text="pas de déphasage (degrés)")

        # stringvar
        self.stringvar_distance_element = tk.StringVar(value="0.05")
        self.stringvar_frequence = tk.StringVar(value="3")
        self.stringvar_frequence.trace("w",
                                       lambda name, index, mode, sv=self.stringvar_frequence:
                                       maj_stringvar(sv,
                                                     self.stringvar_longeur_onde,
                                                     lambda x: 3e8 / (float(x) * 1e9)))
        self.stringvar_longeur_onde = tk.StringVar(value="0.05")
        self.stringvar_pas_de_phase = tk.StringVar(value="0")

        # button
        self.bouton_validation = tk.Button(self.main, text="valider", command=self.maj_figures)
        self.bouton_generation_signal = tk.Button(self.main, text="générer signaux", command=self.start_signaux)
        self.bouton_stop_signal = tk.Button(self.main, text="stopper signaux", command=self.stop_signaux)

        # entry
        self.entry_distance_element = tk.Entry(self.main, textvariable=self.stringvar_distance_element)
        self.entry_frequence = tk.Entry(self.main, textvariable=self.stringvar_frequence)
        self.entry_longeur_onde = tk.Entry(self.main, textvariable=self.stringvar_longeur_onde)
        self.entry_pas_de_phase = tk.Entry(self.main, textvariable=self.stringvar_pas_de_phase)

        # figures
        self.figure_secteur_angulaire = Figure()
        self.figure_zone_visible = Figure()

        # canvas
        self.canvas_secteur_angulaire = FigureCanvasTkAgg(self.figure_secteur_angulaire, master=self.main)
        self.canvas_zone_visible = FigureCanvasTkAgg(self.figure_zone_visible, master=self.main)

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

    def maj_figure_zone_visible(self, pas_de_phase_radians: float, distance_element: float, lmbda: float) -> None:
        """
        Met à jour la figure pour la zone visible avec les paramètres souhaités.
        :param pas_de_phase_radians: pas de phase (en radians) souhaité entre les différents éléments du réseau.
        :param distance_element: distance inter-éléments du réseau (en m)
        :param lmbda: la longueur distance_element'onde (en m)
        :return: None
        """
        self.initialisation_figure_zone_visible()
        data = generer_zone_visible(pas_de_phase_radians, distance_element, lmbda)
        axe = self.figure_zone_visible.gca()
        # axe.set_ylim(0, data["max"])
        axe.set_ylim(-30, 0)

        for x, y, color in data["data"]:
            axe.plot(x*180/np.pi, 10 * np.log(y / data["max"]), color=color)

        self.canvas_zone_visible.draw()

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

    def initialisation_widgets(self) -> None:
        """
        Initialise l'affichage tous les widgets de l'application.
        :return: None
        """
        self.label_distance_elements.pack()
        self.entry_distance_element.pack()
        self.label_frequence.pack()
        self.entry_frequence.pack()
        self.label_longueur_onde.pack()
        self.entry_longeur_onde.pack()
        self.label_pas_de_phase.pack()
        self.entry_pas_de_phase.pack()
        self.bouton_validation.pack()
        self.bouton_generation_signal.pack()
        self.bouton_stop_signal.pack()
        # self.canvas_secteur_angulaire.get_tk_widget().pack()
        self.canvas_zone_visible.get_tk_widget().pack()

    def start_signaux(self):
        carte = ouverture_carte("169.254.114.9", 0)
        type_carte = check_card(carte)
        init_vitesse_sampling(type_carte, carte)
        taille_buffer = init_canaux(carte)
        maj_amplitude(carte)
        pvBuffer = init_buffer(carte, taille_buffer)
        pnBuffer = calcul_signaux(pvBuffer)
        transfert_netbox(carte, pvBuffer, taille_buffer)
        start(carte)
        fermeture_carte(carte)

    def stop_signaux(self):
        carte = ouverture_carte("169.254.114.9", 0)
        stop(carte)
        fermeture_carte(carte)


if __name__ == "__main__":
    main = tk.Tk()
    main_frame = MainFrame(main)
    main_frame.pack()
    main.mainloop()
# todo: basculer le gestionnaire de position sur grid au lieu de pack
# todo: commenter le code
