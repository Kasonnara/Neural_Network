# Code par Kasonnara, 2016, France

import matplotlib.pyplot as plt
import math
import matplotlib
import numpy as np
import time

# ____ A UTILISER ___
#TODO thread_objet = threading.Thread(None,focntion, None, *(paramètre de fonction))
#TODO thread_objet.start()
# TODO pour l'interface :: cf help(plt.connect)
#try:
#except KeyboardInterrupt:

 #TODO animation = animation.FuncAnimation(fig, animate, init_func=init, frames=100, blit=True, interval=20, repeat=False) a utiliser pour repasser les simulation enregistrées
#_____________________


#------------------------------------------------------------------------------------------------------------------------------
#                                                           My_Plot
#les My_Plot génère leur propre subplots et gère seul la gestion des donnée et leur actualisation (quand on le leur ordonne)
#dont ils ont besoin pour afficher des informations dan sl'afficheur auquel il sont associé
#
#------------------------------------------------------------------------------------------------------------------------------
class My_Plot(object):
    """ Abstarct de base des plots"""
    def __init__(self,fig,nbr_Lignes,nbr_colonnes,plot_id, **kwargs):
        self.fig=fig
        self.ax=fig.add_subplot(nbr_Lignes,nbr_colonnes,plot_id)

    def Update(self, **kwargs):
        return False # overridable
    def Reset_Gen(self, **kwargs):
        return False
    def Reset_Simu(self,new_epreuve =None, **kwargs):
        return False # overridable

class Text_Plot(My_Plot):
    def __init__(self, fig, nbr_lignes, nbr_colonnes, plot_id, **kwargs):
        self.fig=fig
        #plot_x = 1 - ((plot_id-1)%nbr_lignes)/nbr_colonnes     #abscisse x [0,1] du coté gauche de l'espace autorisé
        #plot_y = 1 - ((plot_id) //nbr_lignes)/nbr_lignes       #ordonnée y [0,1] du coté bas de l'espace autorisé
        #self.text = fig.text(0.1+plot_x, plot_y-0.2, "")
        x = ((plot_id-1)%nbr_colonnes) / nbr_colonnes
        y = 1-((((plot_id-1)//nbr_colonnes) +1) / nbr_lignes)
        self.text = fig.text(0.15 + 0.8*x, 0.1 + 0.8*y, "")
    def Reset_Gen(self,text="", **kwargs):
        self.text.set_text(text)
        return True
    def Reset_Simu(self, new_epreuve=None, simulation_id = 0, text="", **kwargs):
        self.text.set_text(text)
        return True
    def Update(self, text="", **kwargs):
        self.text.set_text(text)
        return True

class Global_Debug_Plot(Text_Plot):
    """ Debug en texte les infos de base """
    singleton=None # Singleton du plot
    def __init__(self, fig, nbr_lignes, nbr_colonnes, plot_id, **kwargs):
        if Global_Debug_Plot.singleton==None:
            # Création d'un singleton pour ne pas calculer plusieurs fois le debug
            Global_Debug_Plot.singleton=self
            print("Affichage : Initialize debug singleton")
            self.generation_best_individus_id=[]
            self.current_best_individus_id=0
            self.fail_Loop_Count=0
            self.last_Debug_Time=0
            self.low_Mutation_Factor=2
            self.high_Mutation_Factor=2
        super(Global_Debug_Plot,self).__init__(fig, nbr_lignes, nbr_colonnes, plot_id)

    def Reset_Gen(self, fail_loop_count = -1, low_Mutation_Factor=-1, high_Mutation_Factor=-1, **kwargs):
        if Global_Debug_Plot.singleton == self:
            self.fail_loop_count     = fail_loop_count
            self.low_Mutation_Factor = low_Mutation_Factor
            self.high_Mutation_Factor= high_Mutation_Factor
        return super(Global_Debug_Plot,self).Reset_Gen(text="Reseting Generation...\n\n\n")       #TODO edit text

    def Reset_Simu(self, simulation_id = 0, **kwargs):
        if Global_Debug_Plot.singleton == self:
            if simulation_id>1:
                self.generation_best_individus_id.append(str(self.current_best_individus_id))
            else:
                self.generation_best_individus_id=[]
            self.current_best_individus_id=-1
            self.start_Time = time.clock()
        return super(Global_Debug_Plot,self).Reset_Simu(text="Reseting Simulation...\n\n\n")         #TODO edit text

    def Update(self,ind_id=-2, avancement=-1, **kwargs):
        if Global_Debug_Plot.singleton == self:
            IRTime = time.clock() - self.start_Time
            temps_restant=(1-avancement)/(avancement+0.00001) * IRTime
            # formatage des donnée en text
            return super(Global_Debug_Plot,self).Update(
                text="Temps de simulation: {0}min, {1}sec\nTemps restant estimé: {2} min {3} sec\nMutation info:FailCount {4}\n   Mutation Factor: low {5},\n                         high {6}\n\n".format(
                    #round(10/(s.DebugTime-self.last_Debug_Time+0.000001)),  # Tick Per Seconds
                    round(IRTime//60),  round(IRTime%60),                   # temps écoulé en minutes et secondes
                    round(temps_restant//60),  round(temps_restant%60),      # temps restant estimé en minutes et secondes
                    self.fail_loop_count,                                   # Nombre d'echec de la simulation courante
                    self.low_Mutation_Factor,  self.high_Mutation_Factor,   # facteurs de mutation bas et hauts
                )
            )
        else:
            Global_Debug_Plot.singleton.Update(ind_id=ind_id, avancement=avancement, **kwargs)
            self.text.set_text(Global_Debug_Plot.singleton.text.get_text())
        return True
    def __str__(self,actualise=False):
        if actualise:
            Global_Debug_Plot.singleton.Update()
        return Global_Debug_Plot.singleton.text.get_text()

class Orbit_Sim_Debug_Plot(Text_Plot):
    singleton=None # Singleton du plot
    def __init__(self, fig, nbr_lignes, nbr_colonnes, plot_id, **kwargs):
        if Orbit_Sim_Debug_Plot.singleton==None:
            Orbit_Sim_Debug_Plot.singleton=self
            self.system=None
    def Reset_Simu(self,new_epreuve=None, simulation_id=0, **kwargs):
        if Orbit_Sim_Debug_Plot.singleton == self:
            self.system = new_epreuve.system
            return True
        return False
    def Update(self, **kwargs):
        if Orbit_Sim_Debug_Plot.singleton == self:
            if self.system == None:
                print("ERROR: Main Orbit_Sim_Debug_Plot system = None --> Update Impossible")
                return False
            s = self.system
            dt_value,dt_unit= formated_Time_Frame(s.dt) #valeure du pas de temps dans son unité la plus adapté et string de l'unité
            # formatage des donnée en text
            super(Orbit_Sim_Debug_Plot,self).Update(
                "In game {1} per tick: {2}\nDay: {3}\nMeilleur individu info:\n Fitness:{4}\n ID:{5}\n Commandes: \n      avancer:{6}\n      tourner:{7}\n      rotation:{8} {9}\nNombre de vaisseau:  {11} ({10})\n\n                         high {17}".format(
                    dt_unit,  int(dt_value),                                                # pas de temps convertie en unité adapté et le string de son unité
                    math.ceil(s.temps/60/60/24),                                            # Temps total écoulé dans simulation (en jour)
                    s.best_Fitness_ship.relative_id, self.generation_best_individus_id,     # meilleur individu et son numero
                    s.best_Fitness_ship.last_Commande[0],  int(s.best_Fitness_ship.position[2]),  s.best_Fitness_ship.reseau.commandesNoChange,    # information sur ce que fait le meilleur individu
                    len(s.LiteObjects),                                                     # Nombre de vaisseau dans la simulation
                    s.nbr_vaisseaux_restant                                                 # nombre de vaisseaux encore en vie dans la simulation
                )
            )
            self.last_Debug_Time=s.DebugTime
            self.current_best_individus_id=s.best_Fitness_ship.relative_id
        else:
            self.text.set_text(str(Debug_Plot.singleton_global_debug_plot))
        return True

def formated_Time_Frame(t):
    """Convertie un temps en seconde en minute (ou au besoin en heures) et renvoicette valeur convertie ainsi qu'un string de l'unité de mesure retenue
    Note : Utilisé uniquement par l'affichage des FPS / temps de la simulation """
    t=t/60/60
    if t>24:
        return t/24,"days"
    else:
        return t,"hours"
def formateur_global(IRTime=0,  fpt=0, avancement=0,  best_individu=-2,  generation_best_individus_ids=[],  fail_Loop_Count=-1,  low_Mutation_Factor=-1,  high_Mutation_Factor=-1):
    """ DEPRECATED convertie et organise les donnée de l'interface en texte"""
    # avancement = IGTime/IGTime_end
    temps_restant=(1-avancement)/avancement * IRTime

    return "TickPerSeconds: {0}\nTemps de simulation: {1}min, {2}sec\nTemps restant estimé: {3} min {4} sec\nMeilleur individu: {5} ({6})\nMutation info:FailCount {7}\n   Mutation Factor: low {8},\n                         high {9}".format(
        round(fpt),
        IRTime//60,  int(IRTime%60),
        int(temps_restant/60),  int(temps_restant%60),

        best_individu,  ','.join(generation_best_individus_id),
        fail_Loop_Count,
        low_Mutation_Factor,  high_Mutation_Factor,
    )
def formateur_OS(IGTime,  dt,  IGTime_end, BI_id, BIcommandes,BIangle, BICommandeNoChange, nbr_ship, nbr_vaisseaux_restant):
    """ DEPRECATED convertie et organise les donnée de l'interface en texte"""
    dt_value,dt_unit= formated_Time_Frame(dt)
    return "In game {1} per tick: {2}\nDay: {3}\nMeilleur individu info:\n ID:{4}\n Commandes: \n      avancer:{5}\n      tourner:{6}\n      rotation:{7} {10}\nNombre de vaisseau:  {8} ({9})\n\n                         high {17}".format(
        dt_unit,  int(dt_value),
        math.ceil(IGTime/60/60/24),
        BI_id,
        BIcommandes[0],  BIcommandes[1],  int(BIangle),  BICommandeNoChange,
        nbr_ship,  fail_Loop_Count,
        nbr_vaisseaux_restant
    )

class Neural_Plot(My_Plot):
    """ Plot le graph du reseau de neurone """
    def __init__(self, fig, nbr_lignes, nbr_colonnes, plot_id, entries_text_formating="",**kwargs):
        super(Neural_Plot,self).__init__(fig, nbr_lignes, nbr_colonnes, plot_id)
        self.reseaux=None
        self.ax.set_axis_bgcolor("white")
        self.neurone_scale=0
        self.last_induvidu_id=1
        self.entries_text=entries_text_formating
        self.text = None
        self.dim=[]
        self.neur_plots=[] # tableau 2 dimension qui stock la liste des cercle associé a chaque neurones
        self.axiom_plots=[] # tableau de dimension 3 qui stock pour chaque neuronne les plot de ses liens avec les neuronnes précedents
        x = ((plot_id-1)%nbr_colonnes) / nbr_colonnes
        y = 1-((((plot_id-1)//nbr_colonnes) +1) / nbr_lignes)
        self.text = fig.text(0.15 + 0.8*(x+0.01), 0.1 + 0.8*(y +0.02), entries_text_formating +"\nneural entries")
    def Reset_Simu(self, new_epreuve=None ,**kwargs):
        reseaux = new_epreuve.reseaux
        if reseaux==None:
            print("WARNING les reseaux fournis n'existent pas")
            return False
        self.reseaux=reseaux
        new_dim=reseaux[0].get_dim()
        if not self.dim==new_dim:
            self.dim=new_dim
            self.Reset_Dim(new_dim)
            # faire ?? set text : self.entries_text.format([0]*len(neur_plots[0])) ?
    def Reset_Dim(self, new_dim):
        #print("neur plot : new dimension :", new_dim)
        self.ax.clear()
        self.neur_plots=[]
        self.axiom_plots=[]
        adjust_factor=2
        max_dim=max(new_dim)
        last_dim=new_dim[0]
        self.neurone_scale=0.3/max_dim
        for k in range(len(new_dim)+1):
            self.axiom_plots.append([])
            self.neur_plots.append([])
            dim=new_dim[k-1] if k>0 else new_dim[0]
            for n in range(dim):
                self.neur_plots[k].append(
                    self.ax.add_patch(plt.Circle(xy=(adjust_factor*(k/len(new_dim)),-(n+0.5)/dim), radius=self.neurone_scale, color="black")))
                if k>0:
                    self.axiom_plots[k].append([])
                    for n_2 in range(last_dim):
                        plot, =self.ax.plot([adjust_factor*(k-1)/len(new_dim), adjust_factor*(k)/len(new_dim)], [-(n_2+0.5)/last_dim, -(n+0.5)/dim],  color="black")
                        self.axiom_plots[k][n].append(plot)
            last_dim = dim
        self.ax.set_xlim(-0.6, adjust_factor+0.2)
        self.ax.set_ylim(-1.05, 0.05)
        self.ax.xaxis.set_ticks_position('none')
        self.ax.xaxis.set_ticklabels([])
        self.ax.yaxis.set_ticks_position('none')
        self.ax.yaxis.set_ticklabels([])

    def Update(self,ind_id=0, **kwargs):
        individu_a_afficher_id=ind_id
        if self.reseaux==None:
            print("WARNING les reseaux n'existent pas, Update Impossible")
            return False
        #print(self.reseaux[individu_a_afficher_id].save_steps[0])
        text_vals = [self.reseaux[individu_a_afficher_id].save_steps[0][0][n] for n in range(len(self.reseaux[individu_a_afficher_id].save_steps[0][0]))]
        self.text.set_text(self.entries_text.format(*text_vals))
        #print("neur_plots dimension :", [len(couche) for couche in self.neur_plots],"\nsave_step dimension :",[len(couche[0]) for couche in self.reseaux[individu_a_afficher_id].save_steps],"\nreseau dimension :",self.reseaux[individu_a_afficher_id].get_dim())
        for k in range(len(self.neur_plots)):
            for n in range(len(self.neur_plots[k])):
                scale,color=calcul_neur_scale_color(self.reseaux[individu_a_afficher_id].save_steps[k][0][n])
                self.neur_plots[k][n].set_color(color)
                self.neur_plots[k][n].set_radius(self.neurone_scale*scale)
                if not self.last_induvidu_id==individu_a_afficher_id and k>0:
                    poid_max=max(self.reseaux[individu_a_afficher_id].couches[k-1].poids[n],key=abs)
                    for m in range(len(self.axiom_plots[k][n])):
                        chr=hex(int(25*min(10,max(0, -math.log10(abs(self.reseaux[individu_a_afficher_id].couches[k-1].poids[m][n]/poid_max))))))[2:]
                        #TODO verifier le sens d'affichage si les coordonée ne sont pas inversées
                        if len(chr)==1: chr="0"+chr
                        self.axiom_plots[k][n][m].set_color("#" + 3*chr)
        self.ax.set_axis_bgcolor("white" if self.last_induvidu_id==individu_a_afficher_id else "grey")
        self.last_induvidu_id=individu_a_afficher_id
        return True

def calcul_neur_scale_color(neur_value):
    """ Associe une taille et une couleur proportionnelle a une valeur de neurone """
    log=min(20,max(0,-math.log10(abs(neur_value)+(10**(-20) )))) # représente la puissance de 10 de la valeur (bornée par 0 et 20)
    scale= 0.1+(20-log)/20
    value=max(-255, min(255,int(250*neur_value*10**log)))
    color=hex(max(0,value))[2:], hex(max(0,-value))[2:]
    return scale,"#"+"0"*(2-len(color[0]))+color[0]+"00"+"0"*(2-len(color[1]))+color[1]

class Orbite_Plot(My_Plot):
    def __init__(self, fig, nbr_Lignes, nbr_colonnes, plot_id,render_SO=True,render_traj=True, render_ref=True, **kwargs):
        super(Orbite_Plot,self).__init__(fig, nbr_Lignes, nbr_colonnes, plot_id)
        self.system=None
        self.ax.set_axis_bgcolor("black")

        self.render_spaceObject=render_SO
        self.render_trajectoire=render_traj

        self.permanent_plot_data=[]
        self.spaceObject_traj_plot=[]
        self.shapes=[]

        if render_ref:
            self.Generate_Referance_Planete_Orbite(0.387,"Mercure")
            self.Generate_Referance_Planete_Orbite(0.723,"Vénus")
            self.Generate_Referance_Planete_Orbite(1,"Terre","#0A2A0A")
            self.Generate_Referance_Planete_Orbite(1.523,"Mars")
            self.Generate_Referance_Planete_Orbite(5.203,"Jupiter")
            self.Generate_Referance_Planete_Orbite(9.537,"Saturne")
            self.Generate_Referance_Planete_Orbite(19.229,"Uranus")
            self.Generate_Referance_Planete_Orbite(30.069,"Neptune")
            plt.legend()

    def Update(self,borneInf=100, force_display=False,**kwargs):
        if self.system==None:
            print("WARNING le systeme n'existe pas Update imposible de la simulation")
            return False
        for k,space_object in enumerate(self.system.MassivesObjects+self.system.LiteObjects):
            color=space_object.get_Color()
            if color==None:
                if force_display:
                    self.spaceObject_traj_plot[k].set_visible(True)
                else:
                    self.shapes[k].set_visible(False)
                    self.spaceObject_traj_plot[k].set_visible(False)
            else:
                if self.render_spaceObject and not(space_object==self.system.MassivesObjects[0]):
                    try:
                        self.shapes[k].set_xy((space_object.position[0],space_object.position[1]))
                    except:
                        self.shapes[k].center=(space_object.position[0],space_object.position[1])
                    self.shapes[k].set_color(color)
            if not color==None or force_display:
                if self.render_trajectoire and not(space_object==self.system.MassivesObjects[0]):
                    self.spaceObject_traj_plot[k].set_xdata(space_object.trajectoireHistX[-borneInf:-1])
                    self.spaceObject_traj_plot[k].set_ydata(space_object.trajectoireHistY[-borneInf:-1])
                    if not color==None:
                        self.spaceObject_traj_plot[k].set_color(color)
        return True

    def Reset_Simu(self,new_epreuve=None, *args, **kwargs):
        self.system=new_epreuve.system
        #nettoyage et reset des plots permanants
        self.ax.clear()
        self.spaceObject_traj_plot=[]
        self.temp_plot=[]
        self.shapes=[]
        for orbite_ref in self.permanent_plot_data :
            self.ax.add_line(orbite_ref)

        if self.system==None:
            print("WARNING le systeme n'existe pas")
            return False
        for space_object in self.system.MassivesObjects+self.system.LiteObjects :
            # ENREGISTREMENT OBJET GRAPHIQUE, a priori l'objet est déjà ajouté a l'axe mais dans le doute
            self.shapes.append(
                self.ax.add_patch(space_object.get_plot(self.ax)))
            # ENREGISTREMENT TRAJECTOIRE
            self.spaceObject_traj_plot.append(None)
            self.spaceObject_traj_plot[-1],= self.ax.plot(space_object.trajectoireHistX, space_object.trajectoireHistY, color=space_object.color)



        #redimentionnement des axes

        self.ax.set_xlim(-self.system.TailleSystemSolaire, self.system.TailleSystemSolaire*1.4)
        self.ax.set_ylim(-self.system.TailleSystemSolaire, self.system.TailleSystemSolaire)
        return True

    """ génère des données de plot circulaire de rayon 'rayon' en UA, de label 'nom' et de couleur 'color'  """
    def Generate_Referance_Planete_Orbite(self,rayon,nom,color="#151515"):
        plot,=plt.plot([rayon*1.496*10**11*np.cos(o/180*np.pi) for o in range(361)],
                                                [rayon*1.496*10**11*np.sin(o/180*np.pi) for o in range(361)],
                                                label=nom, color=color)
        self.permanent_plot_data.append(plot)


class Stats_Plot(My_Plot):
    def __init__(self, fig, nbr_Lignes, nbr_colonnes, plot_id, **kwargs):
        self.fig=fig

        # on veut mettre deux graph dans la case indiqué donc on recalcul le plot_id correspondanta la même position avec 2 fois plus de lignes
        x,y= (plot_id-1) % nbr_colonnes, (plot_id-1) // nbr_colonnes
        y=2*y
        plot_id=y*nbr_colonnes + x +1

        self.ax1=fig.add_subplot(nbr_Lignes*2,nbr_colonnes,plot_id)
        self.ax1.set_ylim(0,5)
        self.ax2=fig.add_subplot(nbr_Lignes*2,nbr_colonnes,plot_id+nbr_colonnes)
        self.ax2.set_ylim(0.25)

    def Reset_Gen(self, *args,stats=None, **kwargs):
        if not stats==None:
            self.ax1.clear()
            self.ax1.plot([stats["generation"][k] for k in range(len(stats["generation"])) if stats["fitness"][k]<1000],[x/5 for x in stats["fitness"]if x<1000],label="Fit")
            self.ax1.plot(stats["generation"],stats["low_mut_fact"],label="L Mut")
            self.ax1.plot(stats["generation"],stats["high_mut_fact"],label="H Mut")
            self.ax1.set_ylim(0,5)
            self.ax1.set_xlim(0,len(stats["generation"])*1.4)
            self.ax1.legend()
            self.ax2.clear()
            self.ax2.plot(stats["generation"],stats["vainqueurId"],label="Winner", color='g', marker='.',linestyle='w')
            self.ax2.plot(stats["generation"],stats["fail_count"],label="Fails", color="r")
            self.ax2.set_xlim(0,len(stats["generation"])*1.4)
            self.ax2.legend()

#------------------------------------------------------------------------------------------------------------------------------
#                                                               AFFICHEURS
#Chaque afficheur génère une figure et contient un certain nombre de "My_Plot" perméttant d'afficher differentes données
#
#------------------------------------------------------------------------------------------------------------------------------

"""Class abstract des afficheurs"""
class Afficheur_Empty(object):
    def __init__(self, window_name="Empty Affiheur",figsize=(16,8) ,**kwargs):
        print("Initialisation afficheur '",window_name,"'")
        self.fig=plt.figure(window_name, figsize=figsize)
        self.fig.suptitle("Génération numéro {0}, Simulation numéro {1}".format(0, 0),fontsize=15)
        self.sub_plots = {}
    def Update(self, **kwargs):
        if (plt.gcf()==self.fig):
            for plot in self.sub_plots.values():
                plot.Update(**kwargs)
        return True # modify herited class if edited

    def Reset_Simu(self,  simulation_id=0, **kwargs):
        self.fig.suptitle(self.figure_name +", Simulation numéro {0}".format( simulation_id), fontsize=15)
        for plot in self.sub_plots.values():
            plot.Reset_Simu(simulation_id=simulation_id, **kwargs)
        return True
    def Reset_Gen(self,generation_id=0, **kwargs):
        self.figure_name="Génération numéro {0}".format((generation_id), fontsize=15)
        for plot in self.sub_plots.values():
            plot.Reset_Gen(generation_id=generation_id, **kwargs)
        return True

""" Le debug Afficheur est une interface texte servant afficher l'essentiel des informations sans affichage graphique pour les pc ne disposants pas de carte graphique"""

class DebugAfficheur(Afficheur_Empty):
    def __init__(self, Sim_debug_plot_class = Orbit_Sim_Debug_Plot, **kwargs ):
        super(DebugAfficheur,self).__init__(generation_id=0,  simulation_id=0, window_name="Debug ToolBar",figsize=(5,3))
        self.sub_plots["global_debug"] = Global_Debug_Plot(self.fig,2,1,1, **kwargs)
        self.sub_plots["sim_debug"]    = Sim_debug_plot_class(self.fig,2,1,2, **kwargs)
        #Note : Reset_Gen need mutation_factor (low et high) et fail_loop_count
        plt.draw()
        plt.pause(0.01)

class Graphique_Afficheur(Afficheur_Empty):
    """L'Afficheur est une interface graphique complete mais gourmande en ressources, elle affiche notament une visulalisation de la   simulation en cours et du reseau en cours de fonctionnement en plus des informations de Debug Interface
    |
    | A priori aucun paramètre n'est nécessaire mais il est possible d'ajouter:
    |   -'debug_afficheur' (RECOMMANDE) (default None) : pour définir le debug_afficheur de reférence
    |   -'render_SO':bool   (default True) = pour afficher les space_Objects
    |   -'render_traj':bool (default True) = pour afficher les trajectoires
    |   -'render_ref':bool  (default True) = pour afficher les orbites de reférence
    |   -'mode_Stat':bool   (default True) = pour afficher les statistique d'évolution a la place d'une représentation du reseau
    |
    """
    def __init__(self,mode_Stat=False, Sim_debug_plot_class = Orbit_Sim_Debug_Plot, Simulation_plot_class = Orbite_Plot, **kwargs):
        super(Graphique_Afficheur,self).__init__(window_name ="Simulation Neuronal", **kwargs)
        self.sub_plots["simu"]          = Simulation_plot_class(self.fig,1,2,1, **kwargs)
        self.sub_plots["global_debug"]  = Global_Debug_Plot(self.fig,4,2,2, **kwargs)
        self.sub_plots["sim_debug"]     = Sim_debug_plot_class(self.fig,4,2,4, **kwargs)
        self.mode_Stat=mode_Stat
        if mode_Stat:
            self.sub_plots["stats"]     = Stats_Plot(self.fig,2,2,4, **kwargs)
        else:
            self.sub_plots["neural"]    = Neural_Plot(self.fig,2,2,4, **kwargs)
        plt.draw()
        plt.pause(0.01)

if __name__=='__main__':
    print("ERREUR veuillez executer le fichier 'SimulationNeuronnales.py'")
