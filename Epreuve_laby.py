import Epreuves
import DisplayTools as DTools
import numpy as np
import labylol3 as laby
import math
"""
Fichier labyrinthe doit contenir:
    une fonction generate() qui retourne un triplet : (array numpy du labyrinthe, couple_x_y de la position de l'entré, couple_x_y de la position de la sortie)
    une fonction is_walkable(valeur_d'une_case) qui renvoi si cette case peut etre traversé par le joueur
"""

class Epreuve_labyrinthe(Epreuves.Epreuve):
    name = "labylol3"
    entries_text_formating = "Case Droite\n  {0}\nCase Gauche\n  {1}\nCase Haut\n  {2}\nCase Bas\n  {3}\nMémoire 1:\n  {4}\nMémoire 2:\n  {5}"
    def __init__(self, reseaux, id_test, timeout = 30, afficheurs=[], turn_limit = 300, **kwargs):
        self.map, self.entry_pos, self.exit_pos = laby.generate()
        self.init_dist = _dist2(self.entry_pos, self.exit_pos)
        self.turn_limit = turn_limit
        super(Epreuve_labyrinthe,self).__init__(reseaux, id_test, timeout=timeout, distinct_ind = len(reseaux), afficheurs=afficheurs, skipped_frames =-1, **kwargs)

    def init_ind(self, ind_id=0):
        self.cur_pos = self.entry_pos
        self.turn = 0
        #print("    Epreuve_laby : init individu")

    def main(self, ind_id, **kwargs):
        #print("    Epreuve_laby : main")
        pos_voisins =  self._get_pos_voisins(self.cur_pos)
        voisins = self._get_voisin(pos_voisins)
        self.cur_comm = self.reseaux[ind_id].GetState(np.array([voisins]), **kwargs)[0,0]

        self.cur_choice = math.floor(self.cur_comm*1.99)+2


        if laby.is_walkable(voisins[self.cur_choice]):
            self.cur_pos = pos_voisins[self.cur_choice]
            #print("move")
        self.turn += 1
        #print(self.cur_pos)
        return (not self.cur_pos == self.exit_pos) and (self.turn < self.turn_limit)

    def exit_ind(self, ind_id):
        fitness = _dist2(self.exit_pos, self.cur_pos)/self.init_dist
        if fitness == 0 :
            finess = self.turn/1000
        self.reseaux[ind_id].fitness += fitness
        self.reseaux[ind_id].commandesNoChange[0] = self.reseaux[ind_id].commandesNoChange[0] or self.cur_pos == self.entry_pos
        #print("    Epreuve_laby : exit individu")
        #print(self.turn)

    def exit(self):
        super(Epreuve_labyrinthe,self).exit()

    def _get_pos_voisins(self, p1):
        return ((p1[0]+1,p1[1]), (p1[0]-1,p1[1]) ,(p1[0],p1[1]+1) ,(p1[0],p1[1]-1))

    def _get_voisin(self, positions):
        return [self.map[p]/3 if p[0]>=0 and p[0]<len(self.map) and p[1]>=0 and p[1]<len(self.map[0]) else -1 for p in positions ]

    def get_entry(self, ind_id):

        reseau_entry_lenght = 4
        reseau_exit_length = 1

def _dist2(p1,p2):
    return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2

class laby_debug_plot(DTools.Text_Plot):
    singleton=None # Singleton du plot
    def __init__(self, fig, nbr_lignes, nbr_colonnes, plot_id,skipped_frames=0, **kwargs):
        super(laby_debug_plot,self).__init__(fig, nbr_lignes, nbr_colonnes, plot_id,skipped_frames=skipped_frames)
        if laby_debug_plot.singleton==None:
            laby_debug_plot.singleton=self
            self.epreuve=None
            self.last_id = -2
    def Reset_Simu(self,new_epreuve=None, simulation_id=0, **kwargs):
        if laby_debug_plot.singleton == self:
            self.epreuve = new_epreuve
            return True
        return False
    def Update(self,ind_id=-2, turn = -1,**kwargs):
        if laby_debug_plot.singleton == self:
            #print("update singelon")
            if self.epreuve == None:
                print("ERROR: Main laby_debug_plot Données nulles --> Update Impossible")
                return False

            # formatage des donnée en text
            self.text.set_text(
                "Current individu info:\n position : {6}\n Nombre de tour: {0}\n Fitness:{1}\n ID:{2}\n Commandes: {3} : {7}\n   changement:{4}\nNombre d'individus: {5}".format(
                    turn,
                    round(_dist2(self.epreuve.cur_pos, self.epreuve.exit_pos)) ,
                    ind_id,                                              # individu actuel
                    command_to_str_direction(self.epreuve.cur_choice),
                    self.epreuve.reseaux[ind_id].commandesNoChange,      # information sur ce que fait le meilleur individu
                    len(self.epreuve.reseaux),                           # Nombre d'individu dans la simulation
                    self.epreuve.cur_pos,
                    self.epreuve.cur_comm
                )
            )
            #self.last_Debug_Time=s.DebugTime
        else:
            laby_debug_plot.singleton.Update(ind_id=ind_id, turn = turn, **kwargs)
            self.text.set_text(laby_debug_plot.singleton.text.get_text())
        return True
choice_to_str = {0:"Droite",1:"Gauche",2:"Haut",3:"Bas", -2:"Erreur :-2"}
def command_to_str_direction(command):
    return choice_to_str[command]

class laby_plot(DTools.My_Plot):
    def __init__(self, fig, nbr_Lignes, nbr_colonnes, plot_id, render_laby = True, render_player=True, keep_player_rendered = True, **kwargs):
        super(laby_plot,self).__init__(fig, nbr_Lignes, nbr_colonnes, plot_id)
        self.epreuve = None
        self.render_laby = render_laby
        self.render_player = render_player
        self.keep_player_rendered = keep_player_rendered
        self.last_id = -2
        self.last_pos = (-1,-1)
        self.cur_player_color = 4
        self.last_players_color = 5
        self.map = None
        self.toggler = 1
    def Update(self, ind_id = -2, force_display=False,**kwargs):
        if self.epreuve==None:
            print("Affichage: WARNING: le labyrinthe n'existe pas --> Update imposible de la simulation")
            return False
        elif self.render_laby or force_display:
            if self.render_player or force_display:
                if self.keep_player_rendered and not(self.last_id ==-2 or self.last_id == ind_id):
                    self.map[self.last_pos] = self.last_players_color
                    #print("Epreuve laby plot : save new player end")
                self.last_id = ind_id
                current_map = self.map.copy()
                self.toggler= -self.toggler
                current_map[0,0] = 1+self.toggler
                current_map[self.epreuve.cur_pos] = self.cur_player_color + ind_id/100
                self.last_pos = self.epreuve.cur_pos
                laby.display(current_map, self.ax)
            else:
                laby.display(self.map, self.ax)
        return True

    def Reset_Simu(self,new_epreuve = None, *args, **kwargs):
        self.epreuve = new_epreuve
        self.map = self.epreuve.map.copy()
        #print(self.map)
        #print(new_epreuve.map)
        self.last_id = -2
        laby.display(self.epreuve.map, self.ax)
        return True


if __name__=='__main__':
    print("ERREUR veuillez executer le fichier 'SimulationNeuronnales.py'")
