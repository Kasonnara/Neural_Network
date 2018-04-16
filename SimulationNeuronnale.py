#! /usr/bin/python3
# -*- coding: UTF8 -*-
# Code par Kasonnara, 2016, France
"""
Partie principale chargé de l'enchainement des simulations et des générations ainsi que de la séléction des réseaux et des sauvegardes.
"""

## ----- Import ------

import random
import time
import math
import sys #?
import matplotlib.pyplot as plt
import os
import numpy as np
import warnings
import neurone
import DisplayTools as dpt
import SelectionPool
import Epreuves
import Epreuve_laby

import auto_param_config as apc
#import orbiteSimulator

## ----- Constantes -----
GENERATION_STOP=1000
NBR_COUCHES=6
NBR_INDIVIDUS=500
NBR_TEST_PAR_GENERATION=5
current_specie_name="espece_12"
SAVE_PATH=os.path.join("Saves",current_specie_name) # Chemin du dosier de sauvegarde
NBR_POOLS = 1


LOW_MUTATION_VARIATION=0.94
HIGH_MUTATION_VARIATION=1.07

DEBUG_AFFICHEURS=()

## ----- Execution du Machine Learning -----

def Simulate_Generation_pool(pools, epreuve_class, afficheurs, is_first_simu=False, **kwargs):
    """Execute une seule génération, la génération reprend la liste déjà crée de réseaux neurals de la génération précedente mais remodifie juste tous les poids
    PARAMS:
        - pools : SelectionPool list = la liste des pool
        - epreuve_class : Class = la classe de l'épreuve
        -[afficheurs]: [afficheur, ... ] = la liste des afficheurs de l'interface utilisateur, par defaut on reprend l'afficheur global crée a l'import.
    """
    #- - - - - - - - - - Réalisation des Tests - - - - - - - - - -
    random_pool_choice = random.randint(0,len(pools)-1)
    for afficheur in afficheurs :
        afficheur.Reset_Gen(stats=pools[random_pool_choice].stats_dict, generation_id= pools[random_pool_choice].generation, high_Mutation_Factor=pools[random_pool_choice].high_mut_fact, low_Mutation_Factor=pools[random_pool_choice].low_mut_fact, fail_loop_count=pools[random_pool_choice].fail_loop_count)
    plt.draw()
    plt.pause(0.0001)
    if is_first_simu:
        # exeption juste après un reboot on ne simule qu'une fois
        epreuve_class([pool[0] for pool in pools], 0, afficheurs = afficheurs)
    else:
        # cas général
        nbr_tests=NBR_TEST_PAR_GENERATION if not(is_first_simu) else 1
        for id_test in range(nbr_tests):
            reseaux=[]
            for pool in pools:
                for reseau in pool:
                    if reseau.is_valid():
                        reseaux.append(reseau)
            if not len(reseaux) ==0:
                epreuve_class(reseaux, id_test, afficheurs=afficheurs, **kwargs)

    print(" Completed Generation's simulations, analyse...")
    # ----- SELECTION du meilleur individu, élimination des perdants et MUTATIONS-----
    for pool in pools:
        id_vainqueur = pool.Execute_Selection_and_Mutation(is_first_simu=is_first_simu)
    print(" End Generation")

def Simulate_Complete_pool(pools, epreuve, afficheurs, **kwargs):
    """Procédure MAIN
    PARAMS:
        - listes de pools de concuents (les pools ne se concurence pas entre elles, mais dans une pool ses indivdus s'affrontent)
        - epreuve : Epreuve =  l'épreuve à résoudre
        - afficheur : pour l'affichage graphique
    """
    generation = min(pool.generation for pool in pools)
    is_first_simu = pools[0].generation>0
    print("Simulation Start: "+current_specie_name, " at generation ", generation)

    # ----- BOUCLE -----
    while generation<=GENERATION_STOP:
        for pool in pools:
            if pool.generation == 0:
                print("Randommisation totale des poids")
                pool.Set_Randomly()
                pool.Apply_Modif(True)
                #print([r.couches[0].poids[0][0] for r in pool.reseaux])
        # --- SIMULATION ---
        Simulate_Generation_pool(pools, epreuve, afficheurs, is_first_simu=is_first_simu, **kwargs)
        is_first_simu=False
    print("SIMULATION COMPLETE "+time.asctime())



##----- MAIN -----

if __name__=='__main__':
    #-------------------------------CONFIG------------------------------
    # Config par defaut mais surchargeable par l'envoi de paramètres bash
    DEFAULT_CONFIG = {"stats":False, "epreuve":"laby", "nbr_couche":NBR_COUCHES, "nbr_pool":NBR_POOLS, "affichage_complet":False}
    CONFIG = apc.dict_param(DEFAULT_CONFIG, warnings_enabled= True, verbose = False)

    Stats=None # XXX
    mode_Stat = CONFIG["stats"]
    NBR_COUCHES = CONFIG["nbr_couche"]
    NBR_POOLS = CONFIG["nbr_pool"]

    #---------------------------INITIALISATION---------------------------

    print("Initalisation Networks list")
    pools=[]

    if CONFIG["epreuve"] == "orbite":
        # Orbite simulation
        DEBUG_AFFICHEURS=(dpt.DebugAfficheur(Simulation_plot_class = Orbit_Sim_Debug_Plot), dpt.Graphique_Afficheur(Simulation_plot_class = Orbit_Plot, debug_afficheur=DEBUG_AFFICHEURS[0],mode_Stat=mode_Stat, entries_text_formating = Epreuves.Epreuve_Deplacement_Spatial.entries_text_formating),)
        current_specie_name="espece_11"
        for i in range(NBR_POOLS):
            pools.append(SelectionPool.Selection_Pool(neurone.Reseau_Mult_P_P_1, NBR_COUCHES, orbiteSimulator.ColectData(None), 2, specie_id=current_specie_name, nbr_individus=NBR_INDIVIDUS, mut_fact=1, SAVE_PATH=SAVE_PATH))
        print("Simulation Start: "+current_specie_name)
        Simulate_Complete_pool(pools, Epreuves.Epreuve_Deplacement_Spatial)

    elif CONFIG["epreuve"] == "laby":
        laby_afficheurs= ( dpt.DebugAfficheur(Sim_debug_plot_class = Epreuve_laby.laby_debug_plot),)
        if CONFIG["affichage_complet"]:
             laby_afficheurs =  laby_afficheurs + (dpt.Graphique_Afficheur(Sim_debug_plot_class = Epreuve_laby.laby_debug_plot, Simulation_plot_class = Epreuve_laby.laby_plot, mode_Stat=mode_Stat, entries_text_formating = Epreuve_laby.Epreuve_labyrinthe.entries_text_formating),)
        for i in range(NBR_POOLS):
            #Ancienne pools
            #pools.append(SelectionPool.Selection_Pool(neurone.Reseau_Add_1, 5, 4, 1, nbr_mem=2, specie_id="espece_laby_1", nbr_individus=NBR_INDIVIDUS, mut_fact=1, SAVE_PATH=os.path.join("Saves","espece_laby_1")))
            #Nouvelles pools
            pools.append(SelectionPool.No_Winner_Selection_Pool(neurone.Reseau_Add_1, NBR_COUCHES, 4, 1, nbr_mem=2, specie_id="espece_laby_2", nbr_individus=NBR_INDIVIDUS,  mut_rate=0.1,low_mut= 0.05, high_mut = 2, SAVE_PATH=os.path.join("Saves","espece_laby_2")))

        print("Simulation Start: "+current_specie_name)
        Simulate_Complete_pool(pools, Epreuve_laby.Epreuve_labyrinthe, laby_afficheurs, do_save_steps = not mode_Stat)
