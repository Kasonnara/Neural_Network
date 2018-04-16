# Code par Kasonnara, 2016, France
#-------------------PARAMETRE REGLABLES----------------------------------
nbr_Planete=5
MASSE_VAISSEAU=10**7
#simulationTime = 1000 # self.temps de simulation en seconde
AffichageGraphiqueEnTempsReel=True
AfficherLaTrajectoireEnTempsReel=True and AffichageGraphiqueEnTempsReel
nbrDePtsAffiche = 100 # 0 pour toujours afficher tous les points

Rangemasse_etoile=[30,30.1]       # (en puissance de 10) pour réference la masse de notre soleil est 1,989 × 10^30   kg
RangeDistPlanete=[11-30,12-30] # (en puissance de 10) plage de distance possible des planètes pour un soleil de taille minimal
RangeMassePlanetes=[-6,-3]     # (en puissance de 10) plage de masse possible des planètes pour un soleil de taille minimal (pour référence mercure:10^24 kg  jupitère:10^27 kg)

minimum_dt=60*10
starshipForce=0.0001*MASSE_VAISSEAU
globalScaleFactor = 100     #\
planeteScaleFactor = 5      #Facteur de grossisement des corps (affin qu'ils soit visible tout en gardant les même proportion de masses)
shipScaleFactor = 10**6     #/
#------------------------------------------------------------------------
# Note evaluation de vitesse avec %timeit

import neurone
import random
import numpy as np
import matplotlib.pyplot as plt
import time
import itertools #import izip
import math
import sys

# constantes:
colorListe=('r','g','lime','b','c','w')
#masse_etoile=10**(random.randint(Rangemasse_etoile[0]*10,Rangemasse_etoile[1]*10)//10)
G=6.67234 * 10**-11
MASSE_VOLUME=(1/2000*3/4/3.1415)**(1/3) # kg.m^-3


class SpaceObject(object):
    next_id=0
    def __init__(self, system, masse=None, pos_et_vit=None, color=None, name="",relative_id=-1):
        """ initialise un SpaceObject
        PARAMS:
            - system : System = le système de la simulation
            -[masse]: float = la masse de la planète, si laissé a None une valeur aléatoire sera choisie entre la masse terrestre et la masse de jupiter
            -[pos_et_vit]: ((float*float),(float*float)) = la position et la vitesse initiale de l'objet en coordonnées cartesienne, si laissé a None, une valeur aléatoire est choisie.

        """
        self.id=system.next_id
        system.next_id+=1
        self.relative_id=relative_id
        self.system=system

        self.alive=True

        #-- init Masse --
        if not masse == None:
            self.masse=masse
        else:
            self.masse=self.randomMasse()

        #-- init position et vitesse --
        if not pos_et_vit == None :
            self.position,self.vitesse=pos_et_vit
        else:
            self.position,self.vitesse=self.randomPositionVit()
        #-- init Couleur --
        if not color == None:
            self.color=color
        else:
            self.color=random.choice(colorListe)

        #-- init Nom --
        if name=="":
            self.name="OVNI "+str(self.id)
        else:
            self.name=name

        self.rayon=self.CalculRayon(real=True)
        self.realRayon = self.CalculRayon(real=True)
        #-- init Affichage du Corps --
        self.shape=None

        #-- init Trajectoire --

        self.trajectoireHistX=[self.position[0]]
        self.trajectoireHistY=[self.position[1]]


    def randomMasse(self):
        """Choisit une masse aléatoire"""
        return self.system.masse_etoile*10**(random.randint(RangeMassePlanetes[0]*100,RangeMassePlanetes[1]*100)/100)

    def randomPositionVit(self):
        """Calcule une position aléatoire et ensuite une vitesse d'orbite circulaire associé
        PARAMS:
            None
        RETURN
            [(float*float), (float*float)] = position et vitesse en coordonnée cartesienne.
        """
        r=10**(random.randint(RangeDistPlanete[0]*100,RangeDistPlanete[1]*100)/100)*self.system.masse_etoile
        teta=random.randint(0,359)
        return [r*np.cos(teta),r*np.sin(teta)],self.calculOrbitalVitesse(r,teta)

    def calculOrbitalVitesse(self,r,teta, v0 = (0,0)):
        """Calcule la vitesse nécessaire pour avoir une orbite circulaire en fonction de la position donné
        PARAMS:
            - r : float = distance a l'astre attracteur autour duquel se fera l'orbite
            - teta : float = l'angle teta dans le réferentiel cylindrique de l'astre attracteur
            -[v0]: (float*float) = vitesse initiale du corps attracteur (nulle par defaut)
        RETURN:
            [float, flaot] = la vitesse souhaitée en coordonnée cartésienne.
        ERREUR; la vitesse initiale ne marche pas encore car cette fonction ne peux etre apliqué qu'au soleil
        """
        v=(G*self.system.masse_etoile/r)**0.5
        return [-v*np.sin(teta)+ v0[0],v*np.cos(teta)+v0[1]]

    def CalculRayon(self,real=False):
        """Calcul le rayon du SpaceObject
        PARAMS:
            real : bool = Si True  renvoi la valeur réelle du rayon du SO utilisable pour les colisions
                          si False renvoi une valeur amplifié afin que l'objet soit visible à l'écran
        RETURN:
            float = rayon du SpaceObject.
        """
        r= (self.masse)**(1/3)*MASSE_VOLUME
        if real:
            return r
        r=r*globalScaleFactor #grossirement global
        if not self.id == 0 :
            r=r*planeteScaleFactor #grossisement planete
        if self.name=="Vaisseau":
            r=r*shipScaleFactor
        return r

    def getDist(self,spaceObject):
        """calcul la distance entre l'objet courant et celui donné en paramètre
        PARAMS:
            - spaceObject : SpaceObject = le deuxième object
        RETURN:
            float = la distance entre les deux SpaceObject
        """
        return ((self.position[0]-spaceObject.position[0])**2+(self.position[1]-spaceObject.position[1])**2)**0.5

    def CalculateAcc(self): # calcule l'accélération de l'objet généré par les objet de masse non négligées a l'instant donnée
        if not self.alive:
            return [0,0]
        (a1,a2)=0,0
        for spaceobject in self.system.MassivesObjects:
            if not spaceobject==self and spaceobject.alive :
                r=self.getDist(spaceobject)
                ac=spaceobject.masse*G/r**2
                a1+=ac*(-self.position[0]+spaceobject.position[0])/r
                a2+=ac*(-self.position[1]+spaceobject.position[1])/r
        return [a1,a2]
    #def CalculateAcc2(self):
        #return [sum(a) for a in itertools.zip_longest(*(subAndScale(spaceobject.position, self.position, spaceobject.masse*G/self.getDist(spaceobject)**3) for spaceobject in self.system.MassivesObjects))]



    def Next_Vit_Euler(self,dt):# fonction en place
        ac=self.CalculateAcc()
        #print("vitesse :"+str(self.vitesse[0])+" acc:"+str(ac[0]*self.dt/self.vitesse[0])+"%")
        self.vitesse[0]+=ac[0]*dt
        self.vitesse[1]+=ac[1]*dt
    def Next_Pos_Euler(self,dt):# fonction en place
        self.position[0]+=self.vitesse[0]*dt
        self.position[1]+=self.vitesse[1]*dt
        self.trajectoireHistX.append(self.position[0])
        self.trajectoireHistY.append(self.position[1])


    def Next_Pos_Verlet(self,dt,acceleration):# fonction en place, a ne pas appeler Next_Vit_Verley le fait tout seul!!
        self.position = [sum(x) for x in zip(self.position, vScale(self.vitesse,dt), vScale(acceleration,(dt**2)/2))]
        self.trajectoireHistX.append(self.position[0])
        self.trajectoireHistY.append(self.position[1])
        #[ On somme sur chaque composante  dernière position +      vitesse*self.dt          +    acceleration * self.dt**2/2         ]
    def Next_Vit_Verley(self,dt,last_Acceleration,new_Acceleration):# fonction en place
        self.vitesse  = [sum(x) for x in zip(self.vitesse,vScale(last_Acceleration,dt/2),vScale(new_Acceleration,dt/2))]


    def get_plot(self, ax):
        if self.shape==None : self.shape=plt.Circle(xy=(self.position[0],self.position[1]), radius=self.rayon, color=self.color, fill=True, axes=ax, label=self.name)
        else: self.shape.set_axes(ax)
        return self.shape

    def get_Color(self):
        return (self.color if self.alive else None)

    def is_Ship (self):
        return False
    """ verifie que l'objet n'est pas entré en collision avec l'objet en paramètre et au besoin le tue s'il est plus léger que ce dernier"""
    def check_Collision(self, space_object):
        if self==space_object or not self.alive:
            return False
        if self.getDist(space_object) < self.realRayon + space_object.realRayon:
            if self.masse < space_object.masse:
                print("    "+self.name+" crashed on "+space_object.name)
                self.alive=False
                self.system.nbr_vaisseaux_restant-=1
                space_object.masse += self.masse
            return True
        return False

    """ verifie que l'objet n'est pas sortie des limites du systeme solaire et au besoin le tue"""
    def check_limite(self):
        if not self.alive:
            return False
        if self.getDist(self.system.MassivesObjects[0])>self.system.limite:
            print("    "+self.name+" run too far")
            self.alive=False
            self.system.nbr_vaisseaux_restant-=1
            return True
        return False

    def __str__(self):
        return self.name

#-----------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------



class SpaceShip(SpaceObject):
    def __init__(self, system, fitnessFunc, poussee=starshipForce, vitesse_de_rotation=180/minimum_dt, rotation=0, reseau=None,**kwargs):
        super(SpaceShip,self).__init__(system, **kwargs)

        if len(self.position)<3:
            self.position.append(rotation)

        if len(self.vitesse)<3:
            self.vitesse.append(0)

        if not poussee==None:
            self.poussee=poussee
        else:
            print("ERREUR poussé du vaisseau non définie")

        self.vitesse_de_rotation=vitesse_de_rotation
        self.reseau=reseau
        if reseau==None:
            print("ERREUR pas de réseau fournit au vaisseau")

        # init fitness scoring
        self.fitnessfunc=fitnessFunc
        self.score=1000

        self.last_Commande=np.array([[0],[0]])

    def CalculateAcc(self):
        if not self.alive:
            return [0,0,0]
        vAcc=super(SpaceShip,self).CalculateAcc()
        self.last_Commande=self.reseau.GetState(ColectData(self))

        vAcc[0]+=np.cos(self.position[2]/180*np.pi)*self.poussee*self.last_Commande[0][0]/self.masse
        vAcc[1]+=np.sin(self.position[2]/180*np.pi)*self.poussee*self.last_Commande[0][0]/self.masse

        vAcc.append(0)
        self.position[2]=self.position[2]%360
        self.vitesse[2]=self.last_Commande[0][1]*self.vitesse_de_rotation # la commande de rotation se fait en vitesse plutot qu'en accélération
        return vAcc

    def get_plot(self, ax):
        if self.shape==None:
            self.shape=plt.Rectangle((self.position[0],self.position[1]), self.rayon, self.rayon, color=self.color, fill=True,label=self.name, axes=ax)
        else:
            self.shape.set_axes(ax)
            #print("ajustement axe")
        return self.shape
        pass


    def get_Color(self):
        if self.alive==False:
            return None
        if self.system.best_Fitness_ship==self:
            return "red"
        else:
            return self.color

    def is_Ship (self):
        return True

#-----------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------

class System:
    def __init__ (self, masse_etoile=None, nbr_Rand_Planete=1, simulationNumber=1, generationMax=1, afficheurs=None, stats=None):
        """Initialise un systeme qui est le principal élément d'une simulation

        PARAMS:
            -[masse_etoile] : float = (default None, choisi automatiquement une masse aléatoire de l'ordre de 1 à 1000 fois celle du soleil) masse de l'étoile du système
            -[nbr_Rand_Planet]: int = (default 1) nombre de planètes générées aléatoirement
            -[simulationNumber]: int = (default 1) id de la simulation, pas essentiel au fonctionnement mais utile pour l'affichage A VERIFIER avec le nouveau DISPLAYTOOLS
            -[generationNumber]: int = (default 1) id de la génération, pas essentiel au fonctionnement mais utile pour l'affichage A VERIFIER avec le nouveau DISPLAYTOOLS
            -afficheurs
            -stats
        """
        self.genereation_id=generationMax
        self.simulation_id=simulationNumber
        self.next_id=0


        # Génération du systeme
        if masse_etoile==None:
            self.masse_etoile=10**(random.randint(Rangemasse_etoile[0]*10,Rangemasse_etoile[1]*10)//10)
        else:
            self.masse_etoile=masse_etoile

        self.MassivesObjects=[SpaceObject(self, masse=self.masse_etoile, pos_et_vit=([0,0],[0,0]), color='#F4FA58', name="Soleil", relative_id=0)] # liste des objet celestes massif
        self.LiteObjects=[] # liste des objet celestes léger
        self.TailleSystemSolaire=10**RangeDistPlanete[1]*self.masse_etoile

        self.nbr_vaisseaux_restant=0
        self.limite=self.TailleSystemSolaire*2

        # Génération des planetes
        for k in range(nbr_Rand_Planete): # on crée des planetes aléatoires
            self.MassivesObjects.append(SpaceObject(self,relative_id=k+1))
        #raccourcis
        self.SUN=self.MassivesObjects[0]
        self.TARGET=self.MassivesObjects[1]
        self.Fitness_Reference=1

        # STOCKAGE DES DONNEE POUR L'INTERFACE
        self.best_Fitness_ship=None
        self.stats=stats
        #self.best_Fitness_ship_id=0

        self.dt=1
        self.temps =0
        self.DebugTime = 0
        self.lastDebugTime = 0
        self.start_Time=0
        self.runTime = 0

        self.afficheurs=afficheurs #on enregistre l'afficheur
        #for afficheur in self.afficheurs: afficheur.Reset_Simu(self, new_generation_id=generationNumber, new_simulation_id=simulationNumber) # et on le re-initialise  # NE PAS RESET ICI MAIS DANS LA BOUCLE PRINCIPALE APRES QUE TOUS LES SPACE_OBJECT SOIENT CREE


    def Add_Starship(self, fitness_func, **kwargs):
        """Ajoute un vaisseaua la simulation.
        le paramètre reseau doit etre spécifié en premier, la position inital et la rotation initiale doivent etre identique a tous les vaisseau pour une bonne évaluation

        PARAMS:
            - fitness_func : func = la fonction utilisé pour l'évaluation des reseaux
            - reseau : Reseau = le reseau du vaisseau, /!\ même si ce paramètre est un paramètre nommé facultatif cela ne sert qu'a facilement transmettre l'info au travers des couches de fonction et ce paramètre doit absoluement etre spécifié.
            - pos_et_vit : ([x,y],[v_x,v_y]) = la position et la vitesse initiale du vaisseau, /!\ même si ce paramètre est un paramètre nommé facultatif cela ne sert qu'a facilement transmettre l'info au travers des couches de fonction et ce paramètre doit absoluement etre spécifié car a defaut une valeur aléatoire sera choisie hors elles doivent etre identiques a tous les vaisseaux pour une bonne évaluation .
            - rotation : float = rotation initiale du SpaceObject en degré
            -[color] : string = couleur du SpaceObject
            -[name]: string  = nom du SpaceObject
            -[vitesse_de_rotation]: float = vitesse maximal angulaire du vaisseau en degré par seconde (doit etre commune a tout les vaisseaux pour une évaluation équitable), par defaut elle est calculé pour permettre a un vaisseau de faire un demi-tour complet même dans le plus petit interval de temps possible
            -[poussee]: la puissance maximale déployable par le vaisseau (en newton?)

        EFFET DE BORD:
            met a jour la distance initiale de réference pour le fitnesse
        RETURN:
            rien
        """
        # TODO augmenter la securité en imposant de renseigner la position,vitesse et le reseau
        self.LiteObjects.append(SpaceShip(self, fitness_func, masse=MASSE_VAISSEAU, relative_id=len(self.LiteObjects), **kwargs))
        # c'est un peu bizarre de l'évaluer ici car sencée etre la même pour tous les vaisseau (et est d'ailleur a chaque fois écrasé pas un nouveau vaisseau)
        self.Fitness_Reference=abs((self.LiteObjects[-1].getDist(self.SUN))-(self.TARGET.getDist(self.SUN)))


    def SimulateMultiMasseEuler(self,runTime=10,speedFactor=60*60*24*7):

        warnings.warn("deprecated", DeprecationWarning)
        for afficheur in self.afficheurs : afficheur.Reset_Simu(self)
        self.runTime=runTime
        lastTime=time.clock()
        endTime=lastTime+runTime
        self.temps=time.clock()
        while lastTime<endTime:
            lastTime=self.temps
            self.temps=time.clock()

            self.dt=(self.temps-lastTime)*speedFactor
            self.self.dt=self.dt
            for spaceObject in self.MassivesObjects[1:]+self.LiteObjects:
                spaceObject.Next_Vit_Euler(self.dt)
            for spaceObject in self.MassivesObjects[1:]+self.LiteObjects:
                spaceObject.Next_Pos_Euler(self.dt)

                for afficheur in self.afficheurs: afficheur.Update()

        for spaceObject in self.MassivesObjects[1:]+self.LiteObjects: # affichage final des trajectoires
            spaceObject.ActualiseAffichage(True)


    def Simulate_Multi_Masse_Verlet(self,runTime=60*60*24*100, IRLTimeLimit=60*20):
        """Réalise une simulation sur le modèle de VERLET, elle affine aussi le pas de self.temps si nécessaire pour un meilleur rapport vitesse de calcul / prescision

        PARAMS:
            - runTime : float = (en secondes dans la simulation) à simuler
            -[IRLTimeLimit]: float = (en secondes IRL) limite de sécurité de la simulation] si ce temps est atteint la simulation est coupée de force
        RETURN:
            rien
        """
        if len(self.LiteObjects)==0:
            plt.pause(1)
            return

        self.runTime=runTime
        self.nbr_vaisseaux_restant=len(self.LiteObjects)

        self.lastDebugTime,self.DebugTime,self.start_Time=(time.clock(),)*3
        end_Time_Securite= self.start_Time+IRLTimeLimit

        self.best_Fitness_ship=self.LiteObjects[0]



        n=0

        last_Accelerations=[spaceObject.CalculateAcc() for spaceObject in self.MassivesObjects[1:]+self.LiteObjects]
        while  self.temps<self.runTime and self.DebugTime<end_Time_Securite:
            self.dt=get_Optimal_dt(self.MassivesObjects,self.LiteObjects)
            k=0
            for spaceObject in self.MassivesObjects[1:]+self.LiteObjects:
                if spaceObject.alive:
                    # on calcule les nouvelles positions de tous les objet a partir de l'accélération enregistré
                    spaceObject.Next_Pos_Verlet(self.dt,last_Accelerations[k])
                k+=1

            #on actualise toute les nouvelles acclération (en conservant l'ancienne)
            new_Accelerations=[spaceObject.CalculateAcc() for spaceObject in self.MassivesObjects[1:]+self.LiteObjects ]

            k=0
            for spaceObject in self.MassivesObjects[1:]+self.LiteObjects:
                if spaceObject.alive:
                    # on calcule les nouvelle vitesse de tous les objet a partir des accélérations
                    spaceObject.Next_Vit_Verley(self.dt,last_Accelerations[k],new_Accelerations[k])

                    spaceObject.check_limite()
                    for spaceObject_2 in self.MassivesObjects:
                        spaceObject.check_Collision(spaceObject_2)
                k+=1

            self.best_Fitness_ship= min(self.LiteObjects, key=self.LiteObjects[0].fitnessfunc)



            #On efface l'ancienne accélération et on stock la nouvelle pour le prochain cycle
            last_Accelerations=new_Accelerations
            self.lastDebugTime=self.DebugTime
            self.DebugTime=time.clock()
            TPF,unit=formated_Time_Frame(self.dt)

            if self.afficheurs :
                n+=1
                if n==10:
                    n=0
                    for afficheur in self.afficheurs: afficheur.Update(individu_a_afficher_id=self.best_Fitness_ship.relative_id)
            self.temps+=self.dt

        # FIN
        for spaceObject in self.MassivesObjects[1:]+self.LiteObjects: # affichage final des trajectoires
            if spaceObject.is_Ship():
                spaceObject.score=min(spaceObject.score,spaceObject.fitnessfunc(spaceObject))

        for afficheur in self.afficheurs: afficheur.Update(borneInf=0, force_display=True)
        plt.pause(1)
        plt.draw()


#-----------------------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------------------------------
## ----- utilitaires -----

def vSum(L1,L2):
    """SOustrait terme a termes les deux listes
    PARAMS:
        L1 , L2 : listes = listes a soustraires
    RETURN:
        liste = liste de la soustraction terme a termes des deux listes en paramètre"""
    return [sum(x) for x in zip(L1,L2)]
    #return [L1[0]-L2[0], L1[1]-L2[1]]


def vScale(L,scale):
    """multiplie terme a terme la liste par le scalaire
    RETURN:
        la liste où chaque terme est mutiplié le scalaire
    """
    return [x*scale for x in L]



optimalCoef=0.075
def optimal_dt(SP1,SP2):
    """UTILISE UNIQUEMENT par "get_Optimal_dt
    PARAMS:
        SP1, SP2 : SpaceObject *2
    RETURN:
        un pas de temps optimisé pour limiter les calcul quand les objet sont éloignées et affiner la précision quand ils sont proches (ici il s'agit de 0.075 fois le temps necessaires aux astres pour se rejoindre a leur vitesse relative actuelle(s'ils se dirigeaient l'un vers l'autre à la même vitesse)
    """
    v=vSum(SP1.vitesse,vScale(SP2.vitesse,-1))
    return SP1.getDist(SP2)*optimalCoef/(v[0]**2+v[1]**2)**0.5


# calcule get_Optimal_dt pour tous les objets pouvant interagir entre eux et retourne le plus petit self.dt
def get_Optimal_dt(Massives,Lites):
    """calcule le pas de temps optimal pour affiner les calculs lorsque les objets se rapprchent mais calculer plus vite lorsque que   cela n'est pas nécessaire
    PARAMS:
        - Massives,Lites : deux listes de SpaceObject = les listes des objets massifs et légers
    GLOBALPARAMS:
        - minimum_dt : float = limite minimal du pas de temps
    """
    min_dt=optimal_dt(Massives[0],Massives[1])

    for sp1 in Lites:
        if sp1.alive:
            for sp2 in Massives:
                m2=optimal_dt(sp1,sp2)

                if(m2<min_dt):
                    min_dt=m2
    for k in range(len(Massives)-1):
        for l in range(k+1, len(Massives)):

            m2=optimal_dt(Massives[k],Massives[l])

            if(m2<min_dt):
                min_dt=m2

    if(minimum_dt>min_dt):
        min_dt=minimum_dt
    return min_dt


def formated_Time_Frame(t):
    """Utilisé uniquement par l'affichage des FPS et du temps de la simulation
    PARAMS:
        -temps en seconde
    RETURN:
        si le temps est inférieur a une journé renvoi le couple consitué du temps converti en heure et du string "hours"
        sinon renvoi le couple constitué du temps converti en jour et du string "days"

    """
    h=t/60/60
    if h>24:
        return h/24,"days"
    else:
        return h,"hours"

def _Star_Ship_Color(identifier):
    """NOT REALY USED
        retourne une couleur grise variable dégradé selon l'identifiant du vaisseau afin de les reconnaitres.
    PARAMS:
        -identifier : int = identifiant du vaisseau
    RETOUR:
        string = un code html de la couleur a transmettre au vaisseau
    """
    if identifier==0:
        return "#0000BD"
    elif identifier>=0.5:
        return "#848484"
    elif identifier >=0.25:
        return "#585858"
    else:
        return "#2E2E2E"

## ----- Aquisition des entrées des reseaux -----

""""retourne les données necessaire aufonctionnement du réseau formaté dans un tableau numpy en colone, si l e paramètre est None retourne le nombre de données normalement retourné, toutes les données sont rammené a un nombre entre -1 et 1"""
# donnée a récupérer : (toutes les positions seront en coordonnées polaires de l'objet le plus proche du vaisseau)
#                       -position du vaisseau
#                       -vitesse du vaisseau
#                       -rotation du vaisseau
#                       -position de l'objectif
#                       -masse de l'astre attracteur
#                       (-Le dernierpas de self.temps)
#                       (-positions et masses des planetes proches)




def Cartesian_To_PolarElioCentre(vect2,system):
    """Converti un vecteur du plan en coordonnée cartésienne en coordonnée polaire héliocentré

    PARAMS:
        -vect2 [x,y] : [float, float]  = un vecteur du plan en coordonnée cartésienne NON NUL
    RETURN:
        [float, float] = une liste constitué des deux coordonnées polaires hélio-centré r et teta
    """
    r=math.sqrt(vect2[0]**2+vect2[1]**2)
    return [r/system.TailleSystemSolaire, math.atan2(vect2[1],vect2[0])/math.pi]

def Cartesian_To_PolarElioCentre_positive(vect2,system):
    """Converti un vecteur du plan en coordonnée cartésienne en coordonnée polaire héliocentré STRICTEMENT POSITIVES (pour pouvoir y appliquer un log)

    PARAMS:
        -vect2 [x,y] : [float, float]  = un vecteur du plan en coordonnée cartésienne NON NUL
    RETURN:
        [float, float] = une liste constitué des deux coordonnées polaires hélio-centré r et teta strictement positives
    """
    r=math.sqrt(vect2[0]**2+vect2[1]**2)
    return [r/system.TailleSystemSolaire, math.atan2(vect2[1],vect2[0])/(2*math.pi)+0.5]



def ColectData_Polar_ElioCentre(starship):


    if starship==None:
        return 9
    else:
        data=Cartesian_To_PolarElioCentre(starship.position,starship.system) + Cartesian_To_PolarElioCentre(starship.vitesse,starship.system) + [starship.position[2]/180-1] + Cartesian_To_PolarElioCentre(starship.system.MassivesObjects[1].position,starship.system) + [starship.system.masse_etoile*10**-30] + [starship.system.dt]
        return np.array([data])

def ColectData_Polar_ElioCentre_scaledDt(starship):
    """Cf : ColectData_Polar_ElioCentre"""
    if starship==None:
        return 9
    else:
        data=Cartesian_To_PolarElioCentre(starship.position,starship.system) + Cartesian_To_PolarElioCentre(starship.vitesse,starship.system) + [(starship.position[2]%360)/180-1] + Cartesian_To_PolarElioCentre(starship.system.MassivesObjects[1].position,starship.system) + [starship.system.masse_etoile*10**-30] + [starship.system.dt*0.0000011574]
        return np.array([data], dtype='float64',ndmin=2)

def ColectData_Polar_ElioCentre_scaledDt_Positive(starship):
    """Cf : ColectData_Polar_ElioCentre"""
    if starship==None:
        return 9
    else:
        data=Cartesian_To_PolarElioCentre_positive(starship.position,starship.system) + Cartesian_To_PolarElioCentre_positive(starship.vitesse,starship.system) + [(starship.position[2]%360)/360] + Cartesian_To_PolarElioCentre_positive(starship.system.MassivesObjects[1].position,starship.system) + [starship.system.masse_etoile*10**-30] + [starship.system.dt*0.0000011574]
        return np.array([data], dtype='float64',ndmin=2)



LASTEST_COLLECTEUR_ID = "Log_V1"
DATA_COLLECTEUR = {"V1":ColectData_Polar_ElioCentre, "v2":ColectData_Polar_ElioCentre_scaledDt, "Log_V1":ColectData_Polar_ElioCentre_scaledDt_Positive}
# "espece_1", "espece_2" -- > ColectData_Polar_ElioCentre
# toutes les autres jusqu'a "espèce_9" inclues --> ColectData_Polar_ElioCentre_scaledDt
# log après "espèce_10" --> ColectData_Polar_ElioCentre_scaledDt_Positive
def ColectData(starship, entry_id= "Log_V1"):
    """Pour la retro compatibilité toutes les fonctions de collecte des donnée d'entrée des reseaux sont conservée, et a chacune est associé un identifiant qui est enregistré avec la sauvegarde du reseau

    A améliorer :   - fournir non pas les données mais la fonction elle même qui sera ensuite hébergé directement par le reseau
                    - finir de mettre en place les id pour toutes les sauvegardes
    """
    if starship == None:
        if entry_id in DATA_COLLECTEUR .keys():
            return DATA_COLLECTEUR[entry_id](None)
        else:
            return DATA_COLLECTEUR[LASTEST_COLLECTEUR_ID](None)
    else:
        return DATA_COLLECTEUR[starship.reseau.entry_id](starship)


    """
    if not starship==None :
        id
    if id=="espece_1" or id == "espece_2":
        return  ColectData_Polar_ElioCentre(starship)
    else:
        return ColectData_Polar_ElioCentre_scaledDt_Positive(starship)
    """

if __name__=='__main__':
    print("ERREUR veuillez executer le fichier 'SimulationNeuronnales.py'")
