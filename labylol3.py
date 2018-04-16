##imports
import numpy as np
from random import randint
from math import sqrt
import matplotlib.pyplot as plt

##

def initialisation(m): #point de départ, nouvelle carte, nouveau chemin
    map=np.zeros((m,m))#init carte
    Chemin=[]
    a=randint(0,3)
    p0=((randint(0,m-1),0),(randint(0,m-1),m-1),(0,randint(0,m-1)),(m-1,randint(0,m-1)))[a]
    (x,y)=p0
    map[p0]=2
    return(Chemin,map,p0,(x,y))

def avancer(pos,map,Chemin,m):# se déplacer sans contraites sauf bords
    #si sur les bords on dégage
    x=pos[0]
    y=pos[1]
    if x==0:
        x=x+1
        Chemin.append(pos)
    if x==m-1:
        x=x-1
        Chemin.append(pos)
    if y==0:
        y=y+1
        Chemin.append(pos)
    if y==m-1:
        y=y-1
        Chemin.append(pos)
    #on avance
    a=randint(0,3)
    if a==0 and (map[x+1,y]!=1 and map[x+1,y+1]!=1 and map[x+1,y-1]!=1):
        x=x+1
    elif a==1 and (map[x-1,y]!=1 and map[x-1,y+1]!=1 and map[x-1,y-1]!=1):
        x=x-1
    elif a==2 and (map[x,y+1]!=1 and map[x+1,y+1]!=1 and map[x-1,y+1]!=1):
        y=y+1
    elif a==3 and (map[x,y-1]!=1 and map[x+1,y-2]!=1 and map[x-1,y-1]!=1):
        y=y-1
    pos=(x,y)
    map[pos]=1
    return(pos,Chemin)

def dist(a,b):#distance entre deux points
    dist=sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)
    return dist

def stagne(Chemin):#évite le blocage
    i=2
    stagne=True
    while stagne and i<=15:
        if Chemin[-1]!=Chemin[-i]:
            stagne=False
        i=i+1
    return(stagne)

def cheminsec(Chemin,map,m,n):#n nombre de pas
    pos=Chemin[randint(1,len(Chemin)-1)]#point de départ
    for i in range(n*10):
        pos=avancer(pos,map,Chemin,m)[0]

def tri_sortie(map,Chemin,Chemin2,m,p0,distmin): #o veut éviter les sorties trop près de l'entrée et en garder une seule
    A=[] #liste des sorties
    B=[]#sorties assez loin
    for x in Chemin : #on séléctionne les sorties dans Chemin
        if x[0]==0 or x[0]==m-1 or x[1]==0 or x[1]==m-1:
            A+=[x]
            if dist(x,p0)>=distmin:
                B+=[x]
    for x in Chemin2: #on séléctionne les sorties dans Chemin2
        if x[0]==0 or x[0]==m-1 or x[1]==0 or x[1]==m-1:
            A+=[x]
            if dist(x,p0)>=distmin:
                B+=[x]
    a=randint(0,len(B)-1)
    #print(A)
    sort=B[a]
    for x in A:#on "bouche" les autres sorties
        map[x]=0
    for x in B:#on "bouche" les autres sorties
        map[x]=0
    map[sort]=3
    return(map, sort)

##



def laby(m):
    init=initialisation(m)
    map=init[1]
    Chemin=init[0]
    p0=init[2]
    pos=init[3]
    distmin=1.2#distance sortie
    loin=False # tant que pas assez loin
    bord=False # tant qu'on est pas au bord
    while not loin or not bord :
        pos=avancer(pos,map,Chemin,m)[0]
        Chemin.append(pos)
        if pos[0]==0 or pos[0]==m-1 or pos[1]==0 or pos[1]==m-1:#si on est au bord
            bord=True
        else:
            bord=False
        if dist(p0,pos)>m//distmin:#si on est assez loin
            loin=True
        else:
            loin=False
        if len(Chemin)>20:#on évite la stagnation
            if stagne(Chemin):
                init=initialisation(m)
                map=init[1]
                Chemin=init[0]
                p0=init[2]
                pos=init[3]
                #print('balllaalala')
        #print(Chemin)
    #chemin secondaire
    caractsec=10*m#nombre de pas et de chemins sec (2*m pas mal !)
    Chemin2=[]#si on ne veut pas que les chemins secondaires servent de départ
    for i in range(int(caractsec)):
        cheminsec(Chemin,map,m,int(caractsec))
        Chemin.append(pos)#on accepte qu'ils servent de départ
    map, sortie = tri_sortie(map,Chemin,Chemin2,m,p0,distmin)
    map[p0]=2


    return map, p0, sortie

def generate():
    map,pi,pf = laby(15)
    # verifiacteion point de départ
    p_x=pi[0]+0
    p_y=pi[1]+0
    if p_x==0:
        p_x+=1
    elif p_x==14:
        p_x-=1
    elif p_y==0:
        p_y+=1
    elif p_y==14:
        p_y-=1
    else:
        print("erreur labylol3 verification 1")
    if map[p_x,p_y] == 0:
        print("erreur lors de la génération du labyrinthe, reset")
        return generate()
    # verification point d'arrivée
    p_x=pf[0]+0
    p_y=pf[1]+0
    if p_x==0:
        p_x+=1
    elif p_x==14:
        p_x-=1
    elif p_y==0:
        p_y+=1
    elif p_y==14:
        p_y-=1
    else:
        print("erreur labylol3 verification 2")
    if map[p_x,p_y] == 0:
        print("erreur lors de la génération du labyrinthe, reset")
        return generate()
    return map, pi, pf

def is_walkable(value):
    return value>0
def display(map, axe):
    axe.imshow(map.transpose(), interpolation = 'none', origin='lower')
