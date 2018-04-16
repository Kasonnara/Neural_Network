# Code par Kasonnara, 2016, France
"""Une pool est un ensemble d'individus en concurrence
Ce code a pour objectif de gerer les pool

EN DEVELOPPEMENT, CETTE TACHE EST ACTUELLEMENT GEREE PAR SimulationNeuronnale.py
"""

import neurone
import shelve
import os


class Selection_Pool(object):
    """
    Une pool est un ensemble d'individus en concurrence.
    Cette classer sert a faciliter la gestion d'une multitude de pool dans une même simulation. on peut ainsi avoir des évolution séparré d'individu et donc plusieurs résultats finaux mais éventuellement différents critère de séléction ou differentes formes/taille/types de réseau en même temps.

    Methodes :
        - init_from_save: permet d'initialiser un reseau a partir d'un chemin d'accès de sauvegarde
        - Set_Randomly  : reset completement au hasard tous les reseau de la pool (utile au tout debut de la selection normalement)
        - Select        : effectue le processus de selection des reseau les plus performants (methode abstraite qui sera redéfinie pour chauqe type de pool differente)
        - Mutate        : le procédé de mutation étant géré par les reseaux eux même car differente forme de réseaux peuvent nécessiter des fonction demutation differente, cette fonction n'est qu'un appel centralisé de la methode Mutate de chaque reseau de la pool.
    """
    next_id=0
    DEFAULT_STATS={"generation":[0], "fitness":[1.], "vainqueurId":[0], "fail_count":[0], "low_mut_fact":[3.], "high_mut_fact":[3.]}
    def __init__(self, reseau_class, *params_init_reseau, nbr_individus=50, mut_fact=1, SAVE_PATH="Save/", **key_params_init_reseau):
        """
        Initialise la pool
        ->Les paramètres (à l'exeption de SAVE_PATH) sont seulement les valeures par défauts de la pool.
        ->La fonction cherchera toujours à récupérer une éventuelle sauvegardes situé dans 'SAVE_PATH/Pool_<id>/reseau_data' et les valeures enregistré dedans seront prioritaires, si elles existent.

        PARAMS:
            - reseau_class : Class = Classe par défaut des reseaux de la pool, même si ce paramètre peut etre laissé à None si une sauvegarde esiste car il ne sera pas utilisé, il est conseillé de toujours l'indiquer pour être sur de ne pas l'oublié lors de la génération d'une nouvelle session.
            - *params_init_reseau : *tuple = paramètres obligatoire pour initialiser le réseau (jusqu'a présent: nbr_couche_cachées, nbr_entry, nbr_exit)
            -[nbr_individus]: int = nombre d'individu initial (par défaut) de la pool.
            -[low_mut_fact]: float = coéfficient de mutation initial (par défaut) de la pool
            -[SAVE_PATH]: string = Chemin d'accès au dossier de sauvegarde du programme (un dossier nommé 'Pool_*' où *= id de la pool, y sera crée)
            -[**key_params_init_reseau] : **dict = paramètres factultatif pour initialiser le réseau (jusqu'a présent: nbr_memoire)
        """
        #TODO : *args et ** kwargs peuvent passer au travers de la sauvegarde comme valeures par defaut plutot que directement au constructeur de reseau
        print("reseau_class", reseau_class, "params_init_reseau", params_init_reseau, "nbr_individus", nbr_individus,"mut_fact", mut_fact,"kwargs", key_params_init_reseau)
        self.id = Selection_Pool.next_id
        Selection_Pool.next_id += 1

        # Tentative de récupération de la dèrnière sauvegarde, sinon on prend les valeurs par défaut données en paramètre
        self.SAVE_PATH = os.path.join(SAVE_PATH,"Pool_"+str(self.id))
        verify_dir_path(self.SAVE_PATH)
        self.default={"nbr_individus":nbr_individus, "low_mut_fact":mut_fact, "high_mut_fact":mut_fact, "fail_loop_count":0, "reseau":reseau_class(*params_init_reseau,**key_params_init_reseau)}
        #print(self.default["reseau"].__dict__)
        saved_or_defaut_datas = Read_shelve(self.default, self.SAVE_PATH, 'Data_Reseau')

        #enregistrement des valeurs issues de la sauvegarde ou par défauts
        self.low_mut_fact  = saved_or_defaut_datas["low_mut_fact"] +0.
        self.high_mut_fact = saved_or_defaut_datas["high_mut_fact"] +0.
        self.fail_loop_count = saved_or_defaut_datas["fail_loop_count"] +0.

        self.reseaux=[]
        for i in range(saved_or_defaut_datas["nbr_individus"]):
            if saved_or_defaut_datas["reseau"]==None:
                #print("No save --> generating network")
                # pas de sauvegarde on vérifie que la class de reseau a bien été définie
                if reseau_class == None:
                    raise ValueError('Erreur : Class de reseau non indiqué et pas sauvegarde à imiter')
                else:
                    print("Cas IMPOSSIBLE reseau par défaut inexistant")
                    # création d'un reseau aléatoire
                    self.reseaux.append(reseau_class(*params_init_reseau,**key_params_init_reseau))
                    print("Randomize network "+str(i))
                    self.reseaux[i].randomize_Poids()
                    #print("id:",id(self.reseaux[i]))
            else:
                #print("Save found --> copying")
                # sauvegarde existante, imitation du type de class de la sauvegarde et copie des poids
                self.reseaux.append(type(saved_or_defaut_datas["reseau"])(*params_init_reseau,**key_params_init_reseau))
                #if i==1 and id(self.reseaux[1].couches[0].poids[0][0])==id(self.reseaux[0].couches[0].poids[0][0]):
                #    print("id differente création")
                #print("id avant copy",id(self.reseaux[i].couches[0].poids[0][0]))
                self.reseaux[i].Copy_Poids(saved_or_defaut_datas["reseau"].couches.copy())                                       # PROBLEME DE REFERENCE
                #print("poid origin",id(saved_or_defaut_datas["reseau"].couches[0].poids[0][0]))
                self.reseaux[i].generation = saved_or_defaut_datas["reseau"].generation + 0

        # Lecture des statitiques de la sauvegarde si elle existe sinon valeure par defaut
        self.stats_dict = Read_shelve(Selection_Pool.DEFAULT_STATS, self.SAVE_PATH, 'Stats')
    def save(self, file_name="Data_Reseau"):
        """Enregistre toutes les données essentielles de la pool: nombre de réseaux, coefficients de mutation, et données du meilleur individu; dans un fichier de sauvegarde.
        Le file_name peut etre préciser pour effectuer des back_up, la valeur par défaut du path étant celle utilisée pour l'initialisation de la pool cette sauvegarde est necessaire mais vite réecrite.
        -> dans le cas d'une sauvegarde classique 'Data_Reseau' la procédure sauvegarde aussi automatiquement les stats!

        PARAMS:
            -[file_name]: string = (default 'Data_Reseau' fichier de lecture utilisé a l'init) nom du fichier de sauvegarde
        """
        #print(self.__dict__)
        #TODO (si lors d'un réecriture de la classe, la nouvelle sélection conserve plusieurs indvidus cette fonction doit etre réécrite pour tous les garder a la sauvegarde)
        best_id= self.best_id
        data = {"nbr_individu":self.nbr_individus, "low_mut_fact":self.low_mut_fact, "high_mut_fact":self.high_mut_fact, "reseau":self[best_id]}
        Save_shelve(data, self.default, self.SAVE_PATH, file_name)

        if file_name=="Data_Reseau":
            self.save_stats(best_id=best_id)

    def save_stats(self, best_id=None):
        """Sauvegarde les statistiques de la pool dans le fichier de sauvegarde de celle-ci. En théorie cette fonction n'a pas besoin d'être appelé par l'utilisateur car cette opération est autoimatiquement effectuée par la fonction <save> qui devrait en pratique etre appelée a chaque fois qu'une sauvegarde est nécessaire.
        PARAMS:
            rien
        """
        if best_id==None:
            best_id=self.best_id
        if self.generation == self.stats_dict["generation"][-1]:
            self.stats_dict["fitness"][-1] = self[best_id].fitness
            self.stats_dict["vainqueurId"][-1] = best_id
            self.stats_dict["fail_count"][-1] = self.fail_loop_count
            self.stats_dict["low_mut_fact"][-1] = self.low_mut_fact
            self.stats_dict["high_mut_fact"][-1] = self.high_mut_fact
        else:
            self.stats_dict["generation"].append(self.generation)
            self.stats_dict["fitness"].append(self[best_id].fitness)
            self.stats_dict["vainqueurId"].append(best_id)
            self.stats_dict["fail_count"].append(self.fail_loop_count)
            self.stats_dict["low_mut_fact"].append(self.low_mut_fact)
            self.stats_dict["high_mut_fact"].append(self.high_mut_fact)

        Save_shelve(self.stats_dict, Selection_Pool.DEFAULT_STATS, self.SAVE_PATH, 'Stats')

    def Copy_Poids(self, new_reseau):
        """Procedure de copie les poids du reseau init_reseau dans TOUS les reseaux de la pool
        PARAMS:- init_reseau : reseau = reseau (ou pseud reseau) dont on veux copier les poids
        """
        for i in range(self.nbr_individus):
            self.reseaux[i].Copy_Poids(new_reseau.couches)

    def Set_Randomly(self):
        """Execute la randommisation de TOUS les reseaux de la pool"""
        for i in range(self.nbr_individus):
            #print("Randomize network "+str(i))
            self.reseaux[i].randomize_Poids()

    def Mutate(self, *args, **kwargs):
        """Execute la Mutation de TOUS les reseaux de la pool SAUF le premier qui est la vainqueur de la sélection précedente (mais ses copies elles sont modifiées).
        PARAMS:
            -les paramètres à transmetres à la fonction de mutation : mutation_factor
        """
        for i in range(1,self.nbr_individus):
            self.reseaux[i].Mutate(calcul_Mutate_Factor(i, len(self), self.low_mut_fact, self.high_mut_fact), **kwargs)

    def Apply_Modif(self):
        """Load TOUS les reseaux de la pool .
        PARAMS:
            -les paramètres à transmetres à la fonction de mutation : generation.
        """
        generation_read = self.generation
        if self.fail_loop_count==0:
            # chaque pool gère son compteur de génération:
            #   si fail_loop_count>0 alors on a eu un échèc donc pas de changemeent de gènération
            generation_read +=1
        print(" Pool",self.id,"start Génération",str(generation_read))
        self.low_mut_fact = max(self.low_mut_fact, 0.05)
        self.high_mut_fact = min(self.high_mut_fact, 2)
        for i in range(len(self.reseaux)):
            self.reseaux[i].Apply_Modif(generation_read)

    def _Analyse_results(id_vainqueur, is_first_simu=False):
        if is_first_simu:
            #cas particulier du premier tour après un reboot: On affiche juste le resulat enregistré en mémoire donc pas grave s'il echoue on ne fait rien, les valeures de fail_loop_count et de mutation_factor avant le reboot seront conservées
            print("  First simu, analyse esquivée")
        elif id_vainqueur==-1 or (id_vainqueur==0 and not self.generation==0):
            print(" Pool",self.id,": Echec")
            #ECHEC: aucun individu de la pool ne convient
            if self.generation==0:
                # cas particulier au tout début on recrée completement les reseaux de zero plutot que de les muter
                self.fail_loop_count+=1
                #self.Set_Randomly()
            else:
                #Cas général: On adapte les coefficients de mutation
                self.high_mut_fact = self.high_mut_fact*HIGH_MUTATION_VARIATION
                self.low_mut_fact = self.low_mut_fact*LOW_MUTATION_VARIATION
                self.fail_loop_count+=1
                #TODO Add_Stats(generation,base.fitness,id_vainqueur,fail_Loop_Count,low_mutation_factor,high_mutation_factor,Stats)
                self.save()

        else:
            #Résultat de la génération concluants
            print(" Pool",self.id,": Succès, vainqueur",id_vainqueur)

            # --- reset du facteur de mutation a la valeur optimale ---
            self.fail_loop_count = 0
            self.low_mut_fact = SelectionPool.calcul_Mutate_Factor(id_vainqueur,len(self), self.low_mut_fact, self.high_mut_fact)
            self.high_mut_fact = self.low_mut_fact +0.

            # --- Sauvegarde des données ---
            #TODO Add_Stats(generation,base.fitness,id_vainqueur,fail_Loop_Count,low_mutation_factor,high_mutation_factor,Stats)
            self.save()
            if generation%50 ==0:
                # sauvegarde ponctuelle complete du reseau a des fin de statistique ou de vérifications ultérieures plus poussées
                self.save(file_name='Reseau_'+current_specie_name+'_Generation_'+str(generation)+'.txt')

    def Execute_Selection_and_Mutation(self, is_first_simu=False):
        """Selectionne le meilleur individus de la pool, recopie le code génétiques du meilleurs individus sur tous les autres.
        PARAMS:
            None
        RETURN:
            id : int = l'identifiant du meilleur individu
        /!\ cette fonction est une valeur par defaut mais peu etre redéfinie par un classe fille avec un autre procédé de sélection
        """
        print("SELECTION et recopie")
        id = self.best_id
        self.Copy_Poids(self[id])
        self._Analyse_results(id, is_first_simu=is_first_simu)
        print("  Mutate Pool",self.id)
        self.Mutate(self.low_mut_fact, self.high_mut_fact)
        self.Apply_Modif()
        return id

    def _get_bests_individu_id(self):
        """RETURN int : l'id du meilleur individu de la pool (LOURD CAR RECALULE A CHAQUE FOIS)"""
        #TODO AMELIORER AVEC UN CACHE?
        best_fitness = self.reseaux[0].fitness * 1000
        id = -1
        for i in range(len(self.reseaux)):
            # la 2e et 3e condition sont des flags pour éliminer d'office les reseaux à sorties saturées
            if self.reseaux[i].fitness<best_fitness and self.reseaux[i].is_valid:
                best_fitness=self.reseaux[i].fitness
                id=i
        return id
    best_id = property(_get_bests_individu_id)
    best = property(lambda self: self[self.bests_id])
    generation = property(lambda self:self[0].generation)

    ## -- Attributs Spéciaux de Raccourci --
    # Fonction et procédure servant surtout à simplifier l'utilisation mais ne sont pas essentiel au fonctionnement
    # Les paramètres ne sont pas décris car a priori ces fonctions ne seront pas appelé telquel dont les doc-string sont peu utiles

    def __getitem__(self, index):
        """Raccourci pour accéder aux reseau de la pool comme si celle-ci n'était qu'une liste : (ex: pool[5] renvoi la 5e reseau)
        PRECOND:
            index < len(pool)"""
        return self.reseaux[index]

    def __setitem__(self, index, valeur, nouveau_reseau):
        """Raccourci pour copier un reseau dans un reseau de la pool comme si celle-ci n'était qu'une liste : (ex: pool[5] = valeur  copie les donnée de valeur dans le 5e reseau de la pool)
        A noter que seule une copie des attribue est effectuer on ne génère pas de nouveau réseau ni ne lie par référence les réseaux.
        PRECOND:
            index < len(pool)
            le nouveau_reseau a la même dimension que l'ancien"""
        self.reseaux[index].Copy_Poids(nouveau_reseau)

    def __len__(self):
        """Raccourcis pour récupérer la taille de la pool comme pour une list avec len()"""
        return len(self.reseaux)

## ----- Outil de Sauvegarde SHELVE -----

#TODO Eventuellemnt on peut forcer l'enregistrement des défault avec un init  ==> file.setdefault(key, value) ce qui permet par la suite de ne pas se soucier de verifier les défault tout au long de l'execution
def Save_shelve(data_dict, default_dict, directory, filename):
    shelve_file = shelve.open(os.path.join(directory,filename))
    for key in default_dict.keys():
        if key in data_dict.keys():
            shelve_file[key] = data_dict[key]
        else:
            shelve_file[key] = default_dict[key]
    shelve_file.close()

def Read_shelve(default_dict, directory, filename):
    shelve_file = shelve.open(os.path.join(directory,filename))
    result_dict = {}
    for key in default_dict.keys():
        print("key:",key,", default:",default_dict[key])
        result_dict[key]= shelve_file.get(key, default_dict[key])
    shelve_file.close()
    return result_dict

def verify_dir_path(dir_path):
    """Verifie que tous les dossier du chemin existe et dans le cas contraitre les crée
    PARAMS:
        - dir_path : string = chemin d'accès a verifier
    """
    if not os.path.isdir(dir_path):
        print("Les dossiers du chemin (",dir_path,") n'existe pas tous >> Correction ...")
        # décomposition du path en liste de dossier
        head,tail = os.path.split(dir_path)
        dir_list=[tail]
        while not(head==""):
            head,tail = os.path.split(head)
            dir_list.append(tail)
        print(dir_list)
        # verifie l'existance et recréer si besoin chaque dossier un à un
        recomp_path =""
        for dir in reversed(dir_list):
            recomp_path = os.path.join(recomp_path,dir)
            if not os.path.isdir(recomp_path):
                print("Create directory:",recomp_path)
                os.mkdir(recomp_path)
        print("Success")

#-------------------------------------------------------------------------------
def calcul_Mutate_Factor(id_individu, nbr_individu,low_mutation_factor,high_mutation_factor):
    """Calcul le facteur de mutation a donner a chauqe individu afin d'avoir des individu très muté et d'autres peu (répartition pas linéaire mais exponentielle car les valeur de low_mutation_factor tendent vers 0)
    PARAMS:
        - id_individu : int = le numéro de l'individu
        - low_mutation_factor : float = la valeur minimale de mutation des individu
        - high_mutation_factor : float = la valeur maximale de mutation des individu
    """
    if id_individu==0:
        print("WARNING calcul_Mutate_Factor : param id_individu=0")
        return 0 # a priori ne doit pas etre utilisé
    else:
        return low_mutation_factor**(id_individu/nbr_individu)*high_mutation_factor**(1-id_individu/nbr_individu)



class No_Winner_Selection_Pool():
    DEFAULT_STATS={"fitness":([1.],[0]), "vainqueurId":([0],[0]), "fail_count":([0],[0]), "low_mut_fact":([1.],[0]), "high_mut_fact":([1.],[0])}
    def __init__(self, reseau_class, *params_init_reseau, nbr_individus=50, mut_rate=0.1,low_mut= 0.05, high_mut = 2, SAVE_PATH="Save/", **key_params_init_reseau):
        #Calcul de l'id unique de la pool
        self.id = Selection_Pool.next_id
        Selection_Pool.next_id += 1
        #Récupration sauvegarde
        #  Verification du path
        self.SAVE_PATH = os.path.join(SAVE_PATH,"Pool_"+str(self.id))
        verify_dir_path(os.path.join(self.SAVE_PATH,"individus"))
        #Completer les champs manquants
        Complete_shelve_2({"nbr_individus":nbr_individus,"mutation_rate":mut_rate, "low_mut_fact":low_mut, "high_mut_fact":high_mut, "fail_loop_count":0, "generation":0},self.SAVE_PATH,"main_datas")
        #Initialisation / Resauration des données
        saved_datas = Read_shelve_2(self.SAVE_PATH, "main_datas")
        self.low_mut_fact  = saved_datas["low_mut_fact"] + 0.
        self.high_mut_fact = saved_datas["high_mut_fact"] + 0.
        self.fail_loop_count = saved_datas["fail_loop_count"] + 0
        self.mutation_rate = saved_datas["mutation_rate"] + 0.
        nbr_individus = saved_datas["nbr_individus"] + 0
        self.generation = saved_datas["generation"] + 0
        #Si le dossier de sauvegarde des réseaux ne contient pas assez d'individus on complète la liste
        self.individus_PATH = os.path.join(self.SAVE_PATH, "individus")
        for k in range(len(os.listdir(self.individus_PATH)), nbr_individus):
            #path=os.path.join(self.individus_PATH,"challenger_"+str(k))
            #verify_dir_path(path)
            Complete_shelve_2({"reseau":reseau_class(*params_init_reseau,**key_params_init_reseau), "file_name":"reseau_"+str(k), "rang":k}, self.individus_PATH, "challenger_"+str(k))
        #Restauration des réseaux
        #  On lis chaque fichier (shelve) du dossier de sauvegarde des individus et on importe son  contenu : un dictionnaire contenant en particulier le reseau, son dernier classement, son nombre d'échecs
        self.reseau_datas = [Read_shelve_2(self.individus_PATH, individus_files_names[:individus_files_names.find(".db")]) for individus_files_names in os.listdir(self.individus_PATH)[:nbr_individus]]
        #Completion des stats manquantes
        Complete_shelve_2(No_Winner_Selection_Pool.DEFAULT_STATS, self.SAVE_PATH,"stats")
        #Lecture des stats
        self.stats_dict = Read_shelve_2(self.SAVE_PATH,"stats")

    def save(self, special_backup_path_name="", special_backup=None):
        """OProcedure de sauvegarde des individus :
        PARAMS: -[special_backup_path_name]: string = si indiqué il demande l'enregistrement dans un backup, il représente alors le path (a partir de la racine du dossier de global de sauvegarde) du dossier de backup lors d'une sauvegarde complete, dans le cas d'une sauvegarde d'un reseau en particulier représente le chemin complet (nom du fichier inclu, sans extension)
                                                        sinon l'objet sera enregistré a sa position normale.
                -[special_backup]: dict             = Si laissé a None, une sauvegarde complete de tous les reseau est réalisé,
                                                        sinon il représente le dictionnaire du reseau a enregistrer.
        """
        if special_backup == None:
            # sauvegarde de l'intégralité de la pool
            if special_backup_path_name == "":
                #sauvegarde dans le dossier classique par defaut
                special_backup_path_name = self.SAVE_PATH
            else:
                #création d'un backup de l'intégralité de la pool dans le dossier indiqué
                special_backup_path_name= os.path.join(self.SAVE_PATH, special_backup_path_name)
            for individus_data in self.reseau_datas:
                Save_shelve_2(individus_data, os.path.join(special_backup_path_name,"individus"), individus_data["file_name"])
                Save_shelve_2({"nbr_individus":len(self),"mutation_rate":self.mutation_rate, "low_mut_fact":self.low_mut_fact, "high_mut_fact":self.high_mut_fact, "fail_loop_count":self.fail_loop_count},
                               special_backup_path_name,
                               "main_datas")
        else:
            #sauvegarde d'un individu en particulier
            if special_backup_path_name=="":
                #à sa place par defaut
                special_backup_path_name = special_backup["file_name"]
            else:
                #dans un fichier de backup donné
                pass
            Save_shelve_2(special_backup, self.SAVE_PATH, special_backup_path_name)
    def save_stats(self,**kwargs):
        self.stats_dict["fitness"][0].append(self[best_id].fitness)
        self.stats_dict["fitness"][1].append(self.generation)
        self.stats_dict["fail_count"][0].append(self.fail_loop_count)
        self.stats_dict["fail_count"][1].append(self.generation)
        self.stats_dict["low_mut_fact"][0].append(self.low_mut_fact)
        self.stats_dict["low_mut_fact"][1].append(self.generation)
        self.stats_dict["high_mut_fact"][0].append(self.high_mut_fact)
        self.stats_dict["high_mut_fact"][1].append(self.generation)
        Save_shelve_2(self.stats_dict, self.SAVE_PATH, "stats")

    def Copy_Poids(self, new_reseau):
        """Procedure de copie les poids du reseau init_reseau dans TOUS les reseaux de la pool
        PARAMS:- init_reseau : reseau = reseau (ou pseud reseau) dont on veux copier les poids
        """
        for reseau in self:
            reseau.Copy_Poids(new_reseau.couches)

    def Set_Randomly(self):
        """Execute la randommisation de TOUS les reseaux de la pool"""
        for i in range(len(self)):
            print("Randomize network "+str(i))
            self[i].randomize_Poids()

    def Mutate(self, *args, **kwargs):
        """Execute la Mutation de TOUS les reseaux de la pool SAUF le premier qui est la vainqueur de la sélection précedente (mais ses copies elles sont modifiées).
        PARAMS:
            -les paramètres à transmetres à la fonction de mutation : mutation_factor
        """
        print("Warning: ce type de pool execute automatiquement les mutations lors de la selection")

    def Apply_Modif(self, succes):
        """Load TOUS les reseaux de la pool .
        PARAMS:
            -les paramètres à transmetres à la fonction de mutation : generation.
        """
        if succes:
            self.fail_loop_count = 0
            self.generation +=1
        else:
            self.fail_loop_count +=1
        print(" Pool",self.id,"start Génération",str(self.generation))
        self.low_mut_fact = max(self.low_mut_fact, 0.05)
        self.high_mut_fact = min(self.high_mut_fact, 2)
        
        for i in range(len(self)):
            self[i].Apply_Modif(self.generation)

    def Execute_Selection_and_Mutation(self,  is_first_simu=False, **kwargs):
        """Tri les reseaux de la pool selon leur classement,(les reseau non valides sont déclassé au maximum)
        puis mute les reseaux selon leur classement et une valeur aléatoire (n'importe quel reseau peut avoir n'importe quel note (sauf le premier et les non valides))
                                - les mieux notés sont inchangés,
                                - les moyens sont juste mutés,
                                - les mauvais sont réécrits avec les poids d'un meilleur individu puis mutés normalement
                                - les très mauvais sont réécrits puis fortment mutés (ou complètement randomisés pendant les 30 premières générations))"""
        if is_first_simu:
            self.Apply_Modif(False)
        else:
            fitness_results = [reseau.fitness  for reseau in self if reseau.is_valid]
            if len(fitness_results)>0:
                error_value = max(fitness_results)
                best_value = max(fitness_results)
            else:
                print("  Generation FAIL, aucun individus valide")
                for k in range(n):
                    mut_factor = k/n * self.low_mut_fact + (1-(k/n))*self.high_mut_fact
                    self.reseau_datas[k]["reseau"].Mutate(mut_factor+0.05 , mutation_rate = self.mutation_rate*10)
                self.Apply_Modif(False)
            n=len(self)
            if error_value == best_value:
                print("  Generation FAIL,tous les individus sont a égalité")
                for k in range(n):
                    mut_factor = k/n * self.low_mut_fact + (1-(k/n))*self.high_mut_fact
                    self.reseau_datas[k]["reseau"].Mutate(mut_factor+0.05 , mutation_rate = self.mutation_rate)
                self.Apply_Modif(False)
            else:
                self.reseau_datas = sorted(self.reseau_datas, key = lambda r_data: (r_data["reseau"].fitness if r_data["reseau"].is_valid  else error_value))
                for k in range(n):
                    death =  (self.reseau_datas[k]["reseau"].fitness-best_value)/(error_value-best_value)
                    r = random.random()
                    self.reseau_datas[k]["rang"] = k
                    mut_factor = k/n * self.low_mut_fact + (1(-k/n))*self.high_mut_fact
                    if death**3 < r:
                        if self.generation < 20 :
                            # cas très rare dans les 20 premières générations on reset completement
                            self.reseau_datas[k]["reseau"].randomize_Poids()
                        else:
                            #copie puis mutation très importante
                            self.reseau_datas[k]["reseau"].Copy_Poids(self.reseau_datas[randint(0,k-1)]["reseau"])
                            self.reseau_datas[k]["reseau"].Mutate(4*mut_factor, mutation_rate = self.mutation_rate*10)
                    elif death**2<r:
                        #copie puis mutation normale (coef entre 0.05 et 2 proportinellement au classement du reseau, mutation rate 0.1)
                        self.reseau_datas[k]["reseau"].Copy_Poids(self.reseau_datas[randint(0,k-1)]["reseau"])
                        self.reseau_datas[k]["reseau"].Mutate(mut_factor+0.05 , mutation_rate = self.mutation_rate)
                    elif death<r:
                        #simple mutation
                        self.reseaux_data[k]["reseau"].Mutate(mut_factor+0.05 , mutation_rate = self.mutation_rate)
                self.Apply_Modif(True)
                self.save()


    def __getitem__(self, index):
        """Raccourci pour accéder aux reseau de la pool comme si celle-ci n'était qu'une liste : (ex: pool[5] renvoi la 5e reseau)
        PRECOND:
            index < len(pool)"""
        return self.reseau_datas[index]["reseau"]

    def __setitem__(self, index, valeur, nouveau_reseau):
        """Raccourci pour copier un reseau dans un reseau de la pool comme si celle-ci n'était qu'une liste : (ex: pool[5] = valeur  copie les donnée de valeur dans le 5e reseau de la pool)
        A noter que seule une copie des attribue est effectuer on ne génère pas de nouveau réseau ni ne lie par référence les réseaux.
        PRECOND:
            index < len(pool)
            le nouveau_reseau a la même dimension que l'ancien"""
        self.reseau_datas[index]["reseau"].Copy_Poids(nouveau_reseau)
    def __len__(self):
        """Raccourcis pour récupérer la taille de la pool comme pour une list avec len()"""
        return len(self.reseau_datas)

    best = property(lambda self: self[0])

def Complete_shelve_2(default_dict, directory, filename, file_verbose = False):
    """Cette Procédure s'assure que la sauvegarde contient bien au moins les valeurs par défauts
    Cette fonction est donc executer une seule fois, lors de la création d'une nouvelle sauvegarde ou lors de l'ajout de nouvelle données
    [mettre file_verbose a true pour afficher tous les logs]
    Pré-condition : Le path existe (ou au moins les dossiers)
    Postcondition : Toutes les cléf du dictionnaire on une valeur dans le shelve
    """
    if file_verbose:
        print("File : Shelve Completing,",directory,filename)
    shelve_file = shelve.open(os.path.join(directory,filename))
    for key in default_dict.keys():
        shelve_file[key] = shelve_file.get(key, default_dict[key])
        if file_verbose:
            print(" key:",key,", value:",shelve_file[key])
    shelve_file.close()
    if file_verbose:
        print("File : Shelve Close,",filename)

def Save_shelve_2(data_dict, directory, filename, file_verbose = False):
    """Procédure qui sauvegarde undictionnaire dans le fichier shelve au path donné
    [mettre file_verbose a true pour afficher tous les logs]
    Pré-condition : Le path existe (ou au moins les dossiers)
    """
    if file_verbose:
        print("File : Shelve Saving,",directory,filename)
    shelve_file = shelve.open(os.path.join(directory,filename))
    for key in data_dict.keys():
        shelve_file[key] = data_dict[key]
    shelve_file.close()
    if file_verbose:
        print("File : Shelve Close,",filename)

def Read_shelve_2(directory, filename, file_verbose = False):
    """Fonction qui lit et renvoi l'intégralité du dictionnaire contenu dans le shelve
    [mettre file_verbose a true pour afficher tous les logs]
    Pré-condition : -Le path existe (ou au moins les dossiers)
                    -Toutes les cléf du dictionnaire on une valeur dans le shelve
    """
    if file_verbose:
        print("File : Shelve Reading,",directory,filename)
    shelve_file = shelve.open(os.path.join(directory,filename))
    result_dict = {}
    for key in shelve_file.keys():
        if file_verbose :
            print("key:",key,", value:",shelve_file[key])
        result_dict[key]= shelve_file.get(key)
    shelve_file.close()
    if file_verbose:
        print("File : Shelve Close,",filename)
    return result_dict











if __name__=='__main__':
    print("ERREUR veuillez executer le fichier 'SimulationNeuronnales.py'")
