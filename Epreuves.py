# Code par Kasonnara, 2016, France
"""Code destiner a gerer les differentes épreuves pouvant etre soumises au reseau de neurones

Actuellement implémenté:
    - Déplacement spatiaux

En prévision :
    - Resolution de labyrinthe
    - Batailes de robot
    - Robot babyfoot (modèle physique et/ou commande)

"""
import time
import math #?
import warnings
import matplotlib.pyplot as plt

class Epreuve(object):
    """Structure abstraite des Epreuves
    Fixe une structure (initialisation->execution->extraction des resultats), le tout est dirigé automatiquement orchestré par le __init__ de la classe abstraite, les utilisateur n'ont donc qu'à instancier l'objet pour automatiquement lancé l'execution de toute la simulation et récupérer les résultats par effet de bord dans la variable <fitness> des réseaux

    L'intéret de laisser le __init__ gérer la boucle principale est qu'elle intérrompera l'épreuve en route entre deux boucles si celle-ci est trop longue, le _exit se chargeant ensuite d'assurer la bonne récupération des données
    """
    name = "epreuve sans nom" # nom générique de l'épreuve pour l'affichage
    fitness_croissante = True # sens de classement de la fitness, si True cela indique que pour cette épreuve plus la fitness d'un reseau est élévé mieux c'est, inversement si False les meilleurs réseaux auront une fitness plus basse
    def __init__(self, reseaux, id_test, timeout = 60*20, distinct_ind=1, afficheurs=[],skipped_frames = 10, **kwargs):
        """Procédure __init__ abstraite
        Orchestre le bouclage du _main jusqu'a la terminaison (_main renvoi False) ou que <timeout> soit écoulé, puis fini avec _exit

        Les __init__ des classes filles doivent donc :  1) initialiser les donnée de leur épreuve
                                                        2) lancer le super.__init__ en dernier qui elle executera l'épreuve
        PARAMS:
            - id_test : int = le numéro de l'épreuve
            -[ind_timeout]: float = le temps maximum en seconde autorisé pour executer l'épreuve, si le temps alloué a un individu est écoulé l'individus suivant sera executé même si le _main n'a pas retourné False
            -[distinct_ind]: en combien de "parts" le temps doit etre divisé entre les diferent induvidus
        """
        self.afficheurs = afficheurs
        self.reseaux = reseaux
        print("  Start Epreuve",type(self).name,(id_test+1))
        for afficheur in afficheurs:
            afficheur.Reset_Simu(simulation_id=0, new_epreuve = self)
        plt.draw()
        plt.pause(0.0001)
        self.ind_timeout = timeout/distinct_ind
        start_time = time.clock()
        for ind_id in range(distinct_ind):

            end_time = time.clock() + self.ind_timeout
            self.init_ind(ind_id )
            render_counter = 0
            while self.main(ind_id, **kwargs) and time.clock()< end_time:
                #TODO update l'affichage ici, avec éventuellemnt transmission de données au _main pour lui indiquer si l'affichage est complet ou light
                #print("    main Loop")
                if skipped_frames >0 and render_counter % skipped_frames == 0:
                    for afficheur in afficheurs:
                        afficheur.Update(ind_id=ind_id, force_display=False, turn = render_counter, avancement=ind_id/distinct_ind)
                    plt.draw()
                    plt.pause(0.000001)
                render_counter += 1
            self.exit_ind(ind_id)
            for afficheur in afficheurs:
                afficheur.Update(ind_id=ind_id, force_display=True, turn = render_counter)
            plt.draw()
            plt.pause(0.000001)

        self.exit()
        print("  End Epreuve",type(self).name,time.strftime("(durée de simulation: %M min, %S s)",time.localtime(time.clock()-start_time)))
    def init_ind(self, ind_id):
        """ pour l'intitalisation d'un individu en particulier"""
        print("   Epreuves : Empty init induvidu")

    def main(self,ind_id, **kwargs):
        """Fonction _main abstraite
        Toute l'execution bouclé de l'épreuve doit etre efféctuée ici
        PARAMS:
            rien
        RETURN:
            boolean = True pour demander a reboucler si le temps le permet, False pour terminer l'épreuve
        """
        return False

    def exit_ind(self, ind_id):
        """Procédure de fin d'un individu,est executé après la fin d'un individu et avant l'init du suivant"""
        print("    Epreuves : Empty Exit indivdu")

    def exit(self):
        """Procédure _exit abstraite
        Toutes les opérations essentiel a l'arret de l'épreuve doivent etre effectuées ici:
            -> fermeture et enregistrement de données
            -> et surtout EXTRACTION DES RESULTAT de l'épreuve et transmission des FITNESS au reseaux

        """
        print("    Epreuves : Empty Exit")





import random
import orbiteSimulator

## ----- Evaluation des performances -----

def Fitness(space_object):
    """DEPRECATED, Evalue les performance du reseau neuronale. /!\ tout l'historique est passé en revu et donc la fitnesse est recalculée de zéro, donc lourd en calcul.

    PARAMS:
        - space_object : space_ship = le vaisseau dont on veux évaluer la fitness
    RETURN:
        - la distance minimal entre le vaisseau et la planete cible

    """
    warnings.warn("deprecated", DeprecationWarning)
    distMin=space_object.getDist(space_object.system.MassivesObjects[1])
    for k in range(len(spaceObject.trajectoireHistX)):
        distMin=min(distMin, math.fabs((space_object.system.MassivesObjects[1].trajectoireHistX[k]-space_object.trajectoireHistX[k])**2 + (space_object.system.MassivesObjects[1].trajectoireHistY[k]-space_object.trajectoireHistY[k])**2- space_object.system.MassivesObjects[1].realRayon))
    return distMin


def ContinuousFitness(space_object):
    """DEPRECATED, Evalue les performance du reseau neuronale par la distance (vaisseau / cible).

    PARAMS:
        - space_object : space_ship = le vaisseau dont on veux évaluer la fitness
    RETURN:
        - float = la distance actuelle entre le vaisseau et la planete cible
    """
    warnings.warn("deprecated", DeprecationWarning)
    return math.fabs((space_object.system.Massives_objects[1].position[0]-space_object.position[0])**2 + (space_object.system.Massives_objects[1].position[1]-space_object.position[1])**2- space_object.system.MassivesObjects[1].realRayon)

def Relative_Fitness(space_object):
    """DEPRECATED, Evalue les performance du reseau neuronale par la distance (vaisseau / cible).

    PARAMS:
        - space_object : space_ship = le vaisseau dont on veux évaluer la fitness
    RETURN:
        - float = la distance actuelle entre le vaisseau et la planete cible relativement a l'écart de leurs orbites initiaux. 1 correspond a la distance initiale entre les orbites.
    """
    warnings.warn("deprecated", DeprecationWarning)
    return math.fabs(space_object.getDist(space_object.system.TARGET)-space_object.system.MassivesObjects[1].realRayon)/space_object.system.Fitness_Reference

def Update_Valid_Relative_Fitness(spaceship, fitness_func=Relative_Fitness):
    """Met a jour sans la recalculer intégralement, et renvoi la fitness relative d'un vaisseau. Le tout en verifiant que le réseaux est valide

    PARAMS:
        - space_ship : spaceship = le vaisseau a évaluer
        -[fitness_func]: func = la fonction de fitness a utiliser
    RETURN
        float = la fitnesse du vaisseau si celui ci est valide (c.a.d que ses sorties ne saturent pas 0 ou 1)
        ou 1000 dans le cas contraire
    """
    if not spaceship.is_Ship() or spaceship.reseau.commandesNoChange[0] or spaceship.reseau.commandesNoChange[1] or not spaceship.alive:
        return 1000 # reseau non valide
    spaceship.score=min(spaceship.score, fitness_func(spaceship))
    return spaceship.score

def Fitness_Reseau(reseau):
    return reseau.fitness
class Epreuve_Deplacement_Spatial(Epreuve):
    #TODO Transférer dans orbiteSimulator.py
    name = "Deplacement Spatial"
    entries_text_formating = "Position R:       --\n {0:>11.4e}\nPosition O:       --\n {1:>8.4f}\nVitesse R:        --\n {2:>11.4e}\nVitesse O:       --\n {3:>11.4e}\nAngle:             --\n {4:>8.4f}\nPosition cible R:\n {5:>11.4e}\nPosition cible O:\n {6:>8.4f}\nMasse Etoile:   _\n {7:>11.4e}\nPas de temps:  _\n {8:>11.4e}"
    fitness_croissante = False
    def __init__(self, reseaux, id_test, timeout = 60*5, afficheurs=[]):

        reseau_entry_lenght = 9
        # génération du systeme
        self.system=orbiteSimulator.System(nbr_Rand_Planete=1, simulationNumber=id_test+1, generationMax=max([reso.generation for reso in reseaux]), afficheurs=afficheurs)
        # choix random de l'état initial des vaisseau
        pos_et_vit=self.system.MassivesObjects[1].randomPositionVit()
        rot=random.randint(0,359)

        # ajout des vaisseau au systeme
        for i in range(len(reseaux)):
            reseaux[i].commandesNoChange=[True,True]
            self.system.Add_Starship(Update_Valid_Relative_Fitness, reseau=reseaux[i], pos_et_vit=pos_et_vit, rotation=rot, name="Vaisseau "+str(i), color=orbiteSimulator._Star_Ship_Color(i/len(reseaux)))

        for afficheur in afficheurs :
            afficheur.Reset_Simu(self.system, simulation_id=id_test, reseaux=reseaux)

        super(Epreuve_Deplacement_Spatial,self).__init__(id_test, timeout=timeout, afficheurs=afficheurs) # placé au dernier car execute toute l'épreuve

    def main(self,ind_id, timeout = 60*5, **kwargs):
        # TODO adapter au bouclage
        self.system.Simulate_Multi_Masse_Verlet(runTime=60*60*24*10000, IRLTimeLimit=timeout)
        return False

    def exit(self):
        # enregistrement des performance dans les reseau
        for starship in self.system.LiteObjects:
            starship.reseau.fitness+=starship.score

        super(Epreuve_Deplacement_Spatial,self)._exit()


if __name__=='__main__':
    print("ERREUR veuillez executer le fichier 'SimulationNeuronnales.py'")
