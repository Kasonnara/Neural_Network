# Code par Kasonnara, 2016, France
import numpy as np
import random
import math
import warnings

##________________________________________________________________________________________________________________________________________

##                       Génère un réseau neuronnal COMPLET, FEEDFORWARD, évolutionnistes classiques par concurence

            # il peut exploiter un pannel de fonctions de seuil et de mutagene.

            # Amélio potentiel :    -rebouclage interne feedback => Mémoire
            #                       -reduction du nombre de connection pour autant de neuronnes => Economie de puissance
            #                       -Génétique ascendante possible ou supervision

##________________________________________________________________________________________________________________________________________

##----FONCTIONS Compteur de neurone-------------------------------------------
#retournant le nbr de neurone de la couche k sacahnt que si k=-1 ou k=0 on retourn forcement nbr_entry et si k=nbreCouches on retourne forcement nbr_exit

def ConstantNeuroneCount(k,nbrCoucheCachee,nbr_entry,nbr_exit, nbr_mem):
    if k>=nbrCoucheCachee:
        return nbr_exit + nbr_mem
    elif  k<=0:
       return nbr_entry + nbr_mem
    else:
        return  max(nbr_entry,nbr_exit)

##-----FONCTIONS de POIDS INITIAUX--------------------------------------------
"""peu utile en pratique car ne sert que légèrement a la première génération"""

def Random2(nbr_entry):
    return (random.random()-0.5)*10/nbr_entry

##-----------FONCTIONS DE SEUIL------------------------------------------------
def Identite(x):
    return x

def IdentiteBorne(x):
    return  max(-1, min(1,x))

def IdentiteBorneStrictementPositive(x):
    return max(10**(-20), min(1.,x))


def IdentiteBorneStrictementPositive_log(x):
    return max(-46, min(0.,x))

def Heaviside(x):
    if x>0:
        return  1
    else:
        return -1

def Sigmoide(x):
    return 1/(1+ abs(x))

SeuilFuncPack_P =(  IdentiteBorneStrictementPositive,
                        #bloquer le cache reduit le temps de 30%
                    np.vectorize(IdentiteBorneStrictementPositive, otypes= [np.float],cache=False),
                    np.vectorize(IdentiteBorneStrictementPositive_log, otypes= [np.float],cache=False))
SeuilFuncPack_PN =( IdentiteBorne,
                    np.vectorize(IdentiteBorne, otypes= [np.float],cache=False))

##---------FONCTIONS MUTAGENES-----------------------------------------------
# fonction en place car la mutation s'applique toujours a un individu déjà existant(ou au mieu a la copie qu'un d'individu aui elle pourrait justifier une mutation fonctionnelle, de plus plus tard on procedera peut etre par recombinaisons génétique qui créera d'abord tous les nouveau individu de manière fonctionnelle puis on leur applique une mutation en place

#params: poids[les poids a muter],  id_couche[le numero dela couche muté],  generation_factor[un coef quidécroit avec les génération pour affiner les mutation]

def get_Modified_Axiom_params(species_id):
    """ return la valeur minimale des poids du réseau et le pourcentage de chance de modification de chauqe poids en fonction dunuméro de l'espèce a muter.
     Permet de conserver un historique des valeur de mutation utiliéess """
    if species_id<7 :
        return 0,  1,0
    elif species_id<10:
        return 10**-8,  0.025 ,0
    else:
        return 10**-8,  1 ,0.01

poid_min, mutation_Rate, SwitchFactor= get_Modified_Axiom_params(9)
"""def UniformRelativeTotalDeacreasing_Mutation(poids,id_couche,mut_Factor):
    f=mut_Factor*2
    dimx,dimy=poids.shape
    for x in range(dimx):
        for y in range(dimy):
            mutation=poids[x,y]*f*(random.random()-0.5)
            if random.random()<mutation_Rate and poids[x,y]+mutation>poid_min:
                poids[x,y]+=mutation"""
def UniformRelativeTotalDeacreasing_Mutation(poid, id_couche, mut_Factor):
    mutation = poid*mut_Factor*2*(random.random()-0.5)
    if abs(poid + mutation)> poid_min:
        return poid+mutation
    else:
        return poid

def UniformRelativeSwitch_Mutation_2(poid,id_couche,mut_Factor):
    """ Procédure Modifie aléatoirement le poid poids donné en positif ou en négatif proportionnelement a mut_Foctor/2 (id_couche est innutilisé) """
    mutation=poid*mut_Factor*(random.random()-0.5)
    if poid+mutation>poid_min:
        poid+=mutation
##---------FONCTIONS MATRIX-----------------------------------------------

def Low_Mult_Matrix(entry,mat_a,mat_m, Seuil_Funcs_pack):
    """environ 1.7s à 4.5s pour 10000 RENTABLE POUR 0 ou 1 MULTIPLICATION / EQUIVALENT POUR 2 / PLUS LENT POUR 3 ou plus

    /!\ l'utilisation de High_Mult_Matrix ou Low_Mult_Matrix n'est pas équivalente! High utilise des log et par soucis d'efficassité nécessite son entré et sa sortie sont des tuples (valeur, log(valeur))

    PARAMS: -entry matrice ligne d'entrée,
                        l'algo peut etre modifié pour des matrice de plus d'un ligne mais innutile dans notre cas a priori
            -matrice additive: matrice numpy des poids pour la multiplication
            -matrice multiplicative : tableau a deux dimension (numpy ou pas) des poids de multiplication
            -tuple de (fonction de seuil, fonction de seuil vectorisée, fonction de seuil pour logarithme vectorisée) """
    result_A = Seuil_Funcs_pack[1](np.dot(entry,mat_a))
    nb_multi=len(mat_m[0])
    if nb_multi==0 :
        return result_A
    result_M=[[]]
    for l in range(nb_multi):
        p=1
        for n in range(len(mat_m)):
            p=p*(entry[0][n]**mat_m[n][l])
        result_M[0].append(Seuil_Funcs_pack[0])
    return np.concatenate(  (result_A, np.array(result_M))  ,axis=1)

def High_Mult_Matrix(entry,mat_a,mat_m, Seuil_Funcs_pack):
    """ 2.11s avec vectorization optimisée

    /!\ l'utilisation de High_Mult_Matrix ou Low_Mult_Matrix n'est pas équivalente! High utilise des log et par soucis d'efficassité nécessite son entré et sa sortie sont des tuples (valeur, log(valeur))

    PARAMS: -entry un TUPLE (matrice ligne d'entrée, matrice Ligne des log des entrées)
                        l'algo peut etre modifié pour des matrice de plus d'un ligne mais innutile dans notre cas a priori
            -matrice additive: matrice numpy des poids pour la multiplication
            -matrice multiplicative : tableau a deux dimension (numpy) des poids de multiplication
            -tuple de (fonction de seuil, fonction de seuil Vectorisée) """
    s     = Seuil_Funcs_pack[1](  np.dot(entry[0], mat_a)  )
    s_log = Seuil_Funcs_pack[2](  np.dot(entry[1], mat_m)  )

    return (np.concatenate((s, np.exp(s_log)),axis=1), np.concatenate((np.log(s), s_log), axis=1))


##-------------MAIN CLASSES-----------------------------------------------
class Couche_Neurone(object):
    """Cette classe est le modèle de base abstrait des couches de neurones"""
    SORTIE_MIN = 10**-10  #valeur minimal (absolue) que peux prendre un neurone en dessous il automatiquement arrondi a zéro
    SORTIE_MAX = 1        #valeur maximal (absolue) que peux prendre un neurone au dessus il automatiquement arrondi a un
    seuil_function_pack = () # : func tuple = un groupe de fonctions de seuil necessaire au reseau
    def __init__(self,id_couche, *args, **kwargs):
        self.id_couche=id_couche

    def GetState(self,entry, *args,**kwargs):
        pass
    def Mutate(self, *args,**kwargs):
        pass
    def Apply_Modif(self, *args, **kwargs):
        pass


class CoucheNeurone_Add_PN_N_2(Couche_Neurone):
    """Couche de réseau pas COMBINAISONS LINEAIRE avec SEUILS FIXE et fonctionne pour des entré positives et en négatives"""
    seuil_function_pack = SeuilFuncPack_PN # : func tuple = un groupe de fonctions de seuil necessaire au reseau
    def __init__(self, id_couche, nbr_neurones, nbr_entry, seuil_func_packPack=SeuilFuncPack_PN, *args, **kwargs):
        """Initialise la couche de neurone
        PARAMS:
            - id_couche : int = le numero de la couche dans le reseau
            - nbr_neurones : int = le nombre de neurone de la couche
            - nbr_entry : int = le nombre d'entrées du reseau, soit en général le nombre de neurone de la couche précedente
        """
        self.id_couche=id_couche
        self.poids=[[ (random.random()-0.5)*4 for l in range(nbr_neurones)] for k in range(nbr_entry)]
        self.poids_add=None
        #print("poid id",id(self.poids))
        #print("coef id",id(self.poids[0][0]))

    def GetState(self,entry):
        """Execute le reseau, c.a.d calcul les sorties à partir des entrées
        PARAMS:
            entry : (np.array(1 x nbr_entry),) = 1-uplet contenant un tableau numpy de dimension (1,nbr_entry) représentant les resultat de la couche précedente. /!\ c'est un TUPLE, cela est necessaire pour la compatibilité avec les reseaux logarithmiques. Une liste ou un tuple contenant plus d'une valeur sont aussi compatibles

        RETURN:
            (np.array(1 x nbr_entry),) = tableau numpy ligne des sorties de la couche de neurones
        """
        #print(entry[0], self.poids_add)
        combinaisonLin= np.dot(entry[0], self.poids_add)
        return (CoucheNeurone_Add_PN_N_2.seuil_function_pack[1](combinaisonLin),)


    def randomize_Poids(self, func=Random2):

        for k in range(len(self.poids)):
            n = len(self.poids[k])
            for l in range(n):
                self.poids[k][l]=func(n)

    def Copy_Poids(self, nouvelle_couche):
        """copy les poids d'une autre couche de neurone (ou éventuellement d'une pseudo couche contenant un attribut 'poids', utile lors de l'initialisation

        PARAMS:
            -nouvelle_couche : object(avec un attribut poids) = couche contenant les poids a copier

        RETURN:
            rien, fonction par effet de bords
        """
        #self.poids=nouvelle_couche.poids.copy()   ## PROBLÈME isole mal les id des variables
        self.poids = [[coef+0. for coef in neur] for neur in nouvelle_couche.poids]

        #print("poids inside",id(self.poids[0][0]))
    def Mutate(self,generation_factor,mutation_func = UniformRelativeTotalDeacreasing_Mutation, mutation_rate=0.05):
        """Effectue une mutation des poids des neurones de la couche en leur appliquant la fonction donnée en paramètre
        PARAMS:
            - generation_factor : float = un coefficient généralement décroissant avec le nombre de génération effectué utilisé par les fonctions mutagènes pour reduire les mutations avec le temps afin de ne pas tout détruire et affiner l'évolution.
            -[mutation_func]: une fonction mutagène a appliquer aux poids (cf: description des fonction mutagènes plus haut), par dafaut: (UniformRelativeTotalDeacreasing_Mutation)
            -[mutation_Rate] : float = probabilité de mutation d'un neurone
        RETURN:
            X
        """
        # on mute quelques poids
        for k in range(math.ceil(len(self.poids[0])*len(self.poids)*mutation_rate)):
            x=random.randint(0,len(self.poids)-1)
            y=random.randint(0,len(self.poids[x])-1)
            self.poids[x][y] = mutation_func(self.poids[x][y], self.id_couche,generation_factor*2) +0.


    def Apply_Modif(self,*args, **kwargs):
        """Cette fonction doit etre executée au moins une fois après toute modification des poids, le reseau doit etre reload avant utilisation sinon les modification ne seront pas prises en compte
        PARAMS: rien (a part le self)
        """
        self.poids_add=np.array(self.poids)

    def __str__(self):
        """DEPRECATED utiliser les fonction standard
        Convertie les donnée de la couche de neurone en une chaine de caractère séralisé enregistrable et les retournes
        PARAMS: rien (a part le self)
        RETURN: string = compilation des données de la couche en chaine de caractère
        """
        return   ';'.join([','.join([str(poid) for poid in neurone]) for neurone in self.poids])

    @staticmethod
    def todata( string_data):
        """DEPRECATED utiliser les fonction standard
        Convertie les donnée de la chaine de caractère séralisé en paramètre en données et les retournes
        PARAMS:
            - string_data : string = une chaine de caratère contenant les données du réseau (a priori généré par couche.__str__() et sauvegardée)
        RETURN:
            un objet de type 'couche' avec notament l'attribut couche necessaire pour copier les données sur une vrai couche de neurone existante
        """
        return type('couche',(object,), dict( poids= [[float(v) for v in sNeurone.split(',')] for sNeurone in string_data[i+1:].split(';')], nbr_multi=0) )

    def __getstate__(self):
        """ Filtre les données temporaires, pour ne conserver que celles essentielles à une sauvegarde pickle"""
        return {"id_couche":self.id_couche, "poids":self.poids}

    def __setstate__(self, dict_attr):
        """ Init depuis une sauvegarde pickle """
        self.id_couche=dict_attr["id_couche"]
        self.poids=dict_attr["poids"]
        self.poids_add=None


class CoucheNeurone_Mult_P_P_1(CoucheNeurone_Add_PN_N_2):
    """Couche de neurone par COMBINAISON LINEAIRE et par COMBINAISON LOGARITHMIQUE, avec FONCTION DE SEUIL FIXE mais ses entrées/sorties doivent etre forcément POSITIVES STRICTEMENT"""
    seuil_function_pack = SeuilFuncPack_P # : func tuple = un groupe de fonctions de seuil necessaire au reseau
    def __init__(self, id_couche, nbr_neurones, nbr_entry):
        """Initialise la couche de neurone
        PARAMS:
            - id_couche : int = le numero de la couche dans le reseau
            - nbr_neurones : int = le nombre de neurone de la couche
            - nbr_entry : int = le nombre d'entrées du reseau, soit en général le nombre de neurone de la couche précedente
        """
        self.id_couche=id_couche
        self.poids=[[ 10**-20 for l in range(nbr_neurones)] for k in range(nbr_entry)]
        self.nbr_multi=0
        self.poids_add=None
        self.poids_mul=None

    def GetState(self, entry):
        """Execute le reseau, c.a.d calcul les sorties à partir des entrées
        PARAMS:
            entry : (np.array[[valeurs]], np.array[[log(valeurs)]]) = 1-uplet contenant un tableau numpy de dimension (1,nbr_entry) représentant les resultat de la couche précedente et leurs log.
            /!\ c'est un TUPLE, cela est necessaire pour la compatibilité avec les reseaux logarithmiques. Une liste ou un tuple contenant plus d'une valeur sont aussi compatibles
        RETURN:
            (np.array(1 x nbr_entry),np.array(1 x nbr_entry)) = luple des tableaux numpy ligne des sorties de la couche de neurones et leurs logs
        """
        return High_Mult_Matrix(entry, self.poids_add, self.poids_mul, CoucheNeurone_Mult_P_P_1.seuil_function_pack)


    def Copy_Poids(self, nouvelle_couche):
        """copy les poids d'une autre couche de neurone (ou éventuellement d'une pseudo couche contenant un attribut 'poids', utile lors de l'initialisation
        PARAMS:
            -nouvelle_couche : object(avec un attribut poids et nbr_multi) = couche a copier
        RETURN:
            rien, fonction par effet de bords
        """
        self.poids=nouvelle_couche.poids.copy()
        self.nbr_multi=nouvelle_couche.nbr_multi+0

    def randomize_Poids(self, func=Random2):

        for k in range(len(self.poids)):
            n = len(self.poids[k])
            for l in range(len(self.poids[k])):
                self.poids[k][l]=func(n)

    def Mutate(self,generation_factor,mutation_func=UniformRelativeSwitch_Mutation_2, mutation_Rate=0.05):
        """Effectue une mutation des poids des neurones de la couche en leur appliquant la fonction donnée en paramètre
        PARAMS:
            - generation_factor : float = un coefficient généralement décroissant avec le nombre de génération effectué utilisé par les fonctions mutagènes pour reduire les mutations avec le temps afin de ne pas tout détruire et affiner l'évolution.
            -[mutation_func]: une fonction mutagène a appliquer aux poids (cf: description des fonction mutagènes plus haut), par dafaut: (UniformRelativeTotalDeacreasing_Mutation)
            -[mutation_Rate] : float = probabilité de mutation d'un neurone
        Return: ??
        """
        ### TODO a revoir !! et transplanté au reseau sans multiplication
        # on mute quelques poids
        for k in range(len(self.poids[0]*mutation_Rate)):
            x=random.randint(0,len(self.poids)-1)
            y=random.randint(0,len(self.poids[x])-1)
            mutation_func(self.poids[x][y],self.id_couche,generation_factor*2)

        # on mute éventuellement nombre de multiplication de 1 ou -1
        if random.random()>SwitchFactor:
            id=random.randint(0,len(self.poids[0])-1)
            n=len(self.poids[0])-self.nbr_multi
            if id<n:
                # on switch un additif en multiplicatif
                self.nbr_multi+=1
                if not id==n-1:
                    for k in range(len(self.poids)):
                        self.poids[k][id], self.poids[k][n-1] = self.poids[k][n-1], self.poids[k][id]
                    return [(id,n-1)]
                return []
            else:
                 # on switch un multiplicatif en additif
                self.nbr_multi+=-1
                if not id==n:
                    for k in range(len(self.poids)):
                        self.poids[k][id], self.poids[k][n] = self.poids[k][n], self.poids[k][id]
                    return [(id,n)]
                return []
        return []

    def invert_Neurones(self, inversions):
        """ intervertit les poids associées a deux neurones de la couche précedente qui ont été échangés
        params, la liste des couple d'id a inverser"""
        for inv in inversions:
            self.poids[inv[0]],self.poids[inv[1]] = self.poids[inv[1]], self.poids[inv[0]]

    def Apply_Modif(self):
        """après toute modification des poids le reseau doit etre reload avant utilisation sinon les modification ne seront pas prises
        en compte"""
        n=len(self.poids)
        m=n-self.nbr_multi
        #if self.id_couche>=6: print(self.poids)
        self.poids_add=np.array( [self.poids[k][:m] for k in range(n)] )

        self.poids_mul=[self.poids[k][m:] for k in range(n)]
        ## TODO eventuellement on peut arrondir ici les valeurs
    def __str__(self):
        """ DEPRECATED utiliser les fonction standard
        convertie les donnée de la couche de neurone en une chaine de caractère séralisé enregistrable et les retournes"""
        return   str (self.nbr_multi)+"/"+';'.join([','.join([str(poid) for poid in neurone]) for neurone in self.poids])
    @staticmethod
    def todata(string_data):
        """ DEPRECATED utiliser les fonction standard
        convertie les donnée de la chaine de caractère séralisé en paramètre en données et les retourne"""
        i = string_data.find("/")
        nbr_multi=0
        coucheType='A'
        if not i==-1:
            nbr_multi = int(string_data[:i])
            if nbr_multi == None:
                return None
            coucheType='M'
        return type('couche_'+coucheType,(object,), dict(
                            poids= [[float(v) for v in sNeurone.split(',')] for sNeurone in string_data[i+1:].split(';')],
                            nbr_multi=nbr_multi))
    def __getstate__(self):
        """ Filtre les données temporaires, pour ne conserver que celles essentielles à une sauvegarde pickle"""
        return {"id_couche":self.id_couche, "poids":self.poids, "nbr_multi":self.nbr_multi}

    def __setstate__(self, dict_attr):
        """ Init depuis une sauvegarde pickle """
        self.id_couche=dict_attr["id_couche"]
        self.poids=dict_attr["poids"]
        self.nbr_multi = dict_attr["nbr_multi"]
        self.poids_add=None
        self.poids_mul=None

##_____________________________________________________________________________________________________________________________
#
#                                                              CLASS Reseau
#
##_____________________________________________________________________________________________________________________________

class Reseau(object):
    entry_id = "Unknown"
    def __init__(self, nbr_couches_cachees, nbr_entry, nbr_exit, nbr_mem = 0, dimension_calculator=ConstantNeuroneCount, specie_id=""):
        print("Init new reseau with id",id(self))
        self.generation  = 0
        self.fitness = 0
        self.specie_id = specie_id
        self.couches=[]
        self.mem = np.ones((1,nbr_mem))
        self.commandesNoChange = [False for k in range(nbr_exit)]
        self.save_steps=[np.zeros((1, dimension_calculator(k,nbr_couches_cachees,nbr_entry,nbr_exit,nbr_mem))) for k in range(-1,nbr_couches_cachees+1)]
        #print("inital save_step_dim", [len(couche[0]) for couche in self.save_steps])
        #self.save_steps= [np.zeros((1, len(couche.poids))) for couche in self.couches] + [np.zeros((1,len(self.couches[-1].poids[0])))]

    def Copy_Poids(self, nouvelles_couches):
        """copy les poids d'un autre reseau de neurone (ou éventuellement d'une pseudo reseau pour l'initialisation)
        PARAMS:
            -nouvelle_couches : object(avec un attribut poids) list = la listes des couches contenant les poids à copier
        RETURN:
            rien, fonction par effet de bords
        PRECOND: les deux réseau ont même dimensions
        """
        for k in range(len(self.couches)):
            self.couches[k].Copy_Poids(nouvelles_couches[k])

    def Mutate(self,generation_factor,mutation_func=UniformRelativeTotalDeacreasing_Mutation,**kwargs):
        for k in range(len(self.couches)):
            self.couches[k].Mutate(generation_factor,mutation_func=mutation_func,**kwargs)

    def randomize_Poids(self, func=Random2):
        for couche in self.couches:
            couche.randomize_Poids(func=func)

    def Apply_Modif(self,generation):
        """Effectue quelques réglage nécessaire au fonctionnement du réseau. Doit être exécutée au moins une fois juste avant de réutiliser le reseau après des mutations et changement de génération.
        PARAMS:
            -generation : int = la génération actuelle du reseau.
        RETURN:
            None
        """
        self.generation = generation
        self.fitness=0
        self.mem = np.ones((1,len(self.mem[0])))
        self.commandesNoChange=[False,False]
        for k in range(len(self.couches)):
            self.couches[k].Apply_Modif()

    def __getstate__(self):
        """ Filtre les données temporaires, pour ne conserver que celles essentielles à une sauvegarde pickle"""
        return {"generation":self.generation, "couches":self.couches, "specie_id":self.specie_id, "nbr_mem":len(self.mem[0])}

    def __setstate__(self, dict_attr):
        """ Init depuis une sauvegarde pickle """
        self.couches = dict_attr["couches"]
        self.generation = dict_attr["generation"]
        self.fitness = 0
        self.specie_id = dict_attr["specie_id"]
        self.commandesNoChange = [False,False]
        self.save_steps= [np.zeros((1, len(couche.poids))) for couche in self.couches] + [np.zeros((1,len(self.couches[-1].poids[0])))]
        self.mem = np.ones((1,dict_attr["nbr_mem"]))

    def GetState(self,entry, do_save_steps=False,**kwargs):
        """Execute le reseaux, c.a.d returne les sorties du reseau en fonction de l'entré donnée
        PARAMS:
            - entry : numpy.array(1 x nbr_entry) = un tableau numpy ligne des entrées
            -[do_save_step] : bool = si True l'étatde chaque neurone sera stocké en mémoire pour affichage, si False il sera perdu
        EFFET DE BORD:
            - si do_save_step vaut True, les valeurs des neurones sont stckées dans self.save_steps
            - actualise la validation du reseau (stockées dans self.commandesNoChange)
        RETURN:
            numpy.array(1 x nbr_sortie) = valeur de sortie du reseau
        TODO : remplacé des entrée en numpy array en liste simple (même si c'est potentiellement moins rapide, c'est plus cohérent et detoute façon la matrice numpy est perdu entre les appels)
        """
        #print("\nReseau: entrée",entry,"entry mémoire", self.mem)
        entry = np.concatenate((entry,self.mem),axis=1)
        exit=(entry,)
        if  do_save_steps:
            self.save_steps[0]=exit[0].copy()
        for couche in self.couches:
            exit=couche.GetState(exit)
            if  do_save_steps:
                self.save_steps[couche.id_couche+1]=exit[0].copy()
        t_y = len(exit[0][0])-len(self.mem[0])
        #print(t_y,exit[0][0,t_y:])
        self.mem = exit[0][0,t_y:].reshape(1,len(self.mem[0]))
        out = exit[0][0,:t_y]
        self.Security_Validation_2(out)
        #("\nRéseau: exit",exit[0][0,:t_y].reshape(1,t_y)," exit mémoire",self.mem)
        return out.reshape(1,t_y)

    def Security_Validation_2(self, commandes):
        """Un reseau qui s'obstine a renvoyer les valeur extremes n'a que peu d'intérêt cette fonction verifie donc si les sortie du reseau sont convenables, un flag boolean (initialisé a True) est associé a chaque sortie du reseau, dès que celle-ci est valide ne seraisse qu'une fois dans la simulation le flag passe à False.
        Note: normalment le reseau réalise tout seul cette opération après chaque GetState, vous ne devriez donc pas avoir a l'utiliser.
        Note_bis: /!\ le param est une liste de sortie a verifier correspondant commandesNoChange(en taille et en sens)! pas la matrice sortante de la couche.
        PARAMS:
            - commandes : list(de taille nbr_exit) = les sorties du reseau
        EFFET_DE_BORD:
            actualise la valeur des flag dans self.commandesNoChange
        """
        #print("commandes",commandes," no change",self.commandesNoChange) # TODO trouver pourquoi au premier tour commandeNoChange a une valeur de trop
        self.commandesNoChange = [self.commandesNoChange[k] and (abs(commandes[k])>=type(self.couches[0]).SORTIE_MAX or abs(commandes[k])<=type(self.couches[0]).SORTIE_MIN) for k in range(len(commandes))]
        #self.commandesNoChange = [
        #    self.commandesNoChange[0]
        #    and (abs(commandes[0][0])>=Couche_Neurone.SORTIE_MAX
        #        or abs(commandes[0][0])<=Couche_Neurone.SORTIE_MIN),
        #    self.commandesNoChange[1]
        #    and (abs(commandes[0][1])>=Couche_Neurone.SORTIE_MAX
        #        or abs(commandes[0][1])<=Couche_Neurone.SORTIE_MIN)]
        #return self.commandesNoChange[0] or self.commandesNoChange[1]

    def is_valid(self):
        invalide = False
        #print(self.commandesNoChange)
        for f in self.commandesNoChange:
            invalide = invalide or f
        return not invalide

    def get_dim(self):
        """Donnes les dimension du reseaux, c.a.d le nombre de neurone de chaqu'une des couches
        PARAMS:
            rien (a part le self)
        RETURN:
            int list : la liste des nombres de neurones de chaque couches
        """
        return [len(self.couches[k].poids[0]) for k in range(len(self.couches))]

class Reseau_Add_1(Reseau):
    """Alloue l'espace necessaire pour un reseau:
    PARAMS:
        - nbr_couches_cachees : int = nombre de chouches caché du reseau, le reseau a donc au final (n+1) couche de neurone au final
        - nbr_entry : int = nombre de valeures donnée en entrée du reseau
        - nbr_exit : int = nombre de valeures attendues en sortie du reseau
        -[dimension_calculator]: func = fonction dont le role est de renvoyer le nombre de neurone de chaque couches en fonction du nombre d'entrées et de sorties du reseau.
        -[specie_id] : string = un string propre a chaque tentative d'apprentissage, elle permet de retrouver toutes les caractéristique de l'essai notament les entrées du reseau.

    """
    entry_id = "Add_V1"
    def __init__(self, nbr_couches_cachees, nbr_entry, nbr_exit, nbr_mem = 0, dimension_calculator=ConstantNeuroneCount, specie_id=""):
        super(Reseau_Add_1, self).__init__(nbr_couches_cachees, nbr_entry, nbr_exit, nbr_mem = nbr_mem, dimension_calculator=ConstantNeuroneCount, specie_id=specie_id)
        self.couches=[CoucheNeurone_Add_PN_N_2(k,dimension_calculator(k,nbr_couches_cachees,nbr_entry,nbr_exit, nbr_mem), dimension_calculator(k-1, nbr_couches_cachees, nbr_entry, nbr_exit, nbr_mem))
        for k in range(nbr_couches_cachees+1)]          # DEPRECATED
    #    print("couches id ", id(self.couches[0]))
class Reseau_Mult_P_P_1(Reseau):
    """Alloue l'espace necessaire pour un reseau:
    PARAMS:
        - nbr_couches_cachees : int = nombre de chouches caché du reseau, le reseau a donc au final (n+1) couche de neurone au final
        - nbr_entry : int = nombre de valeures donnée en entrée du reseau
        - nbr_exit : int = nombre de valeures attendues en sortie du reseau
        - nbr_mem :int = nombre de neuronnes de mémoire (en sortie et en entrée du réseau, ne sont pas comptés dans nbr_entry et nbr_exit)
        -[dimension_calculator]: func = fonction dont le role est de renvoyer le nombre de neurone de chaque couches en fonction du nombre d'entrées et de sorties du reseau.
        -[specie_id] : string = un string propre a chaque tentative d'apprentissage, elle permet de retrouver toutes les caractéristique de l'essai notament les entrées du reseau.

    """
    entry_id = "Log_V1"
    def __init__(self, nbr_couches_cachees, nbr_entry, nbr_exit, nbr_mem = 0, dimension_calculator=ConstantNeuroneCount, specie_id="",):
        super(Reseau_Add_1, self).__init__(nbr_couches_cachees, nbr_entry, nbr_exit, nbr_mem = nbr_mem, dimension_calculator=ConstantNeuroneCount, specie_id=specie_id)
        self.couches=[CoucheNeurone_Mult_P_P_1(k,dimension_calculator(k,nbr_couches_cachees,nbr_entry,nbr_exit, nbr_mem), dimension_calculator(k-1, nbr_couches_cachees,nbr_entry,nbr_exit, nbr_mem))
        for k in range(nbr_couches_cachees+1)]

    def Mutate(self,generation_factor,mutation_func=UniformRelativeSwitch_Mutation_2):
        inversions=[] # memoire tampon des inversion, sert a transmetre a la couche suivante qu'une inversion a été effectuée
        for k in range(len(self.couches)):
            self.couches[k].invert_Neurones(inversions)
            inversions = self.couches[k].Mutate(generation_factor,mutation_func=mutation_func)

    #def __str__(self):
    #    """ DEPRECATED utiliser les fonction standard
    #    convertie les donnée du reseau en une chaine de caractère séralisé enregistrable et les retournes"""
    #    return '\n'.join([ str(couche) for couche in self.couches])

    #@staticmethod
    #def todata(string_data_list):
    #    """ DEPRECATED utiliser les fonction standard
    #    convertie les donnée de la liste chaine de caractère séralisé en paramètre en données et les enregistre dans le reseau
    #    retourne les donnée converties note les donnée sont a priori une liste de tuple (poids, nbr_multi) avec nbr_multi = None si innexistant dans la chaine de caractère (trop vieux par exemple ou erroné) """
    #    data=[]
    #    for k in range(len(string_data_list)):
    #        data.append(CoucheNeurone_Mult_P_P_1.todata(string_data_list[k]))
    #    return data


    def GetState(self,entry, do_save_steps=False):
        """Execute le reseaux, c.a.d returne les sorties du reseau en fonction de l'entré donnée
        PARAMS:
            - entry : numpy.array(1 x nbr_entry) = un tableau numpy ligne des entrées
            -do_save_step : bool = si True l'étatde chaque neurone sera stocké en mémoire pour affichage, si False il sera perdu
        EFFET DE BORD:
            -si do_save_step vaut True, les valeurs des neurones sont stckées dans self.save_steps
            -actualise la validation du reseau (stockées dans self.commandesNoChange)
        RETURN:
            numpy.array(1 x nbr_sortie) = valeur de sortie du reseau
        """
        entry = np.concatenate((entry,self.mem),axis=1)
        exit=(entry,np.log(entry))
        if  do_save_steps:
            self.save_steps[0]=exit[0].copy()

        for couche in self.couches:
            exit=couche.GetState(exit)
            if  do_save_steps:
                self.save_steps[couche.id_couche+1]=exit[0].copy()
        self.Security_Validation_2(exit[0][0])
        t_y = len(exit[0][0])-len(self.mem)
        self.mem = exit[0][0][:t_y].reshape(1,len(slef.mem))
        return exit[0][0][:t_y].reshape(1,t_y)

if __name__=='__main__':
    print("ERREUR veuillez executer le fichier 'SimulationNeuronnales.py'")
