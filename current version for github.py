import http.client
import tkinter as tk 
from tkinter import *
import re
#import copy
import math

global token
token = {
        'Content-Type': "application/json",
        'Authorization': "Bearer TOKEN GOES HERE"        }


EIDtable=[2398,2418,2383,2402,2405,2406,2412,2399,2417,2407] #hard coding this for now, in the future I should probably enable looking up/grabbing EIDs
names=['Shriekwing"','Huntsman Altimor"','Hungering Destroyer"','Lady Inerva Darkvein"','Sun King\'s Salvation"',"Artificer Xy\'mox\"",'Council of Blood"','Sludgefist"','Stone Legion Generals"','Sire Denathrius"']


##########################################
def parse_position(report,start,end,boss_npcID,local_boss_ID):
    #print(report,start,end,boss_npcID,local_boss_ID)
    conn = http.client.HTTPSConnection("www.warcraftlogs.com")
    payload = str("{\"query\":\"{\\n  reportData {\\n    report(code: \\\"")+str(report)+str("\\\") {\\n      events(startTime: ")+str(start)+str(", endTime: ")+str(end)+str(", killType: Kills, hostilityType:Enemies, dataType: DamageTaken, limit: 10000, includeResources: true, targetInstanceID: ")+str(local_boss_ID)+str(" \\n      )\\n        {data nextPageTimestamp}\\n    }\\n  }\\n}\\n\"}")
    headers =token
    conn.request("POST", "/api/v2", payload, headers)
    res = conn.getresponse()
    data = res.read()
    #cleaning the data up a bit
    k=data.decode("utf-8").split("{\"timestamp\":")
    hasNPT=(k[-1].split('"nextPageTimestamp":'))
    NPT = hasNPT[-1].strip('}')
    hasxy=[]
    for i in k:
        if re.search((str("\"targetID\":")+str(boss_npcID)+str(".+\"x\":.+")),i):
                hasxy.append(i.split(',')) #if it has an x coordinate, then throw it in our list as a self contained list of all of the returned parameters
    #NOT ALL OF THE ENTITIES IN OUR LIST HAVE THE X/Y COORDS AT THE SAME INDEX. 
    TXY=[]
    for a in hasxy:
        ph=0
        for b in a:
          if (re.search('\"x\":',b)):# janky, but it finds where theres an x coordinate
              TXY.append([a[0],b,a[ph+1]]) #then slaps the corresponding timestamp, the x and the y into TXY
          ph+=1
    #print('len(TXY)',len(TXY))
    return ([NPT,TXY])
#grabs the start time, end time, and encounter ID for the slection (EID NOT USED, BUT LEAVING IT HERE FOR FUTURE EXTENSIONS)
def get_start_end_EID(report,selection):
    
    conn = http.client.HTTPSConnection("www.warcraftlogs.com")
    payload = str("{\"query\":\"{\\n    reportData {\\n    report(code: \\\"")+str(report)+str("\\\"){fights(killType:Kills){name startTime endTime encounterID}}}}\\n\"}")
    headers = token
    conn.request("POST", "/api/v2", payload, headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    s1=data.split('"name":"')
    s2=[]
    for i in range (1,len(s1)):
        s2.append(s1[i].split(','))
        s2[i-1][1]=s2[i-1][1].strip('startTime":')
        s2[i-1][2]=s2[i-1][2].strip('"endTime":')
        s2[i-1][3]=s2[i-1][3].strip('"encounterID":')
        s2[i-1][3]=s2[i-1][3].strip('}')
        s2[i-1][3]=s2[i-1][3].strip(']')
        s2[i-1][3]=s2[i-1][3].strip('}')# I DO NOT KNOW WHY I NEED TO DO THIS TWICE, BUT IF I DONT, IT LEAVES AN EXTRA }
    for i in s2:
        #print(i)
        if selection==i[0]:
            return [i[1],i[2],i[3]]


def TXY_to_TM(TXY,interval=.2500): #formats the Timestamps and the coordinates into a usable format of [time,total distance moved during that interval]
    #print('in TXY to TM',len(TXY))
    #for i in TXY: print(i)
    Current_interval=[]
    #print(TXY)
    
    initial = float(TXY[0][0])
    #initial cleanup and formatting of TXY:
    for i in range (0,len(TXY)):
        #convert time into seconds, and start the counting at 0, rather than at UTC
        TXY[i][0]=round((float(TXY[i][0])-initial)/1000,4)
        wew=''
        lad=''
        #get rid of the "x/y": shit:
        for k in range (4,len(TXY[i][1])):
            wew+=TXY[i][1][k]
            lad+=TXY[i][2][k]
        TXY[i][1]=round(int(wew)/100,2)
        TXY[i][2]=round(int(lad)/100,2)

    TM=[] #holds the time that's elapsed, and how much movement has occurred. 
    for i in TXY:
        #print(i)
        if len(Current_interval) ==0:
            Current_interval.append(i)
        else:
            if i[0] - Current_interval[0][0] <= interval:
                Current_interval.append(i)
            else:
                Xs=[]
                Ys=[]
                for k in Current_interval:
                    #print(k[1],k[2],Current_interval[0][1],Current_interval[0][2])
                    Xs.append(round(abs(abs(k[1])-abs(Current_interval[0][1])),2))
                    Ys.append(round(abs(abs(k[2])-abs(Current_interval[0][2])),2))
                dxy= round(math.sqrt(max(Xs)**2 + max(Ys)**2),2)
                TM.append([Current_interval[0][0],dxy])
                Current_interval=[]
    #for i in TM: print(i)
    return TM



    #move_threshold:    the minimum distance the move must cover to be inclduded in the results (unit it yards)
    #Twindow:           time between moves before the movement is confirmed as having ended (unit is seconds)
def movement_intervals(TM,move_threshold=3,Twindow=2 ):
    #print('in Move_intervals',len(TM))
    moves=[]
    mStart=0
    mRunTot=0
    mEndFinder=0
    for i in range (0,len(TM)):
        if i==0: #is this the very first iteration of the loop?
            mStart=TM[i][0] 
            mRunTot=TM[i][1]
        else: #if not the very first itteration
            if TM[i][1]>0: # was there any movement in this interval?
                if mRunTot==0:
                    #is it new movement?
                        mStart=TM[i][0]
                        mEndFinder = TM[i][0]
                        mRunTot=TM[i][1]
                else:
                    #or is it a continuation
                        mEndFinder = TM[i][0]
                        mRunTot+=TM[i][1]
 
            else: #if no movement:
                if TM[i][0]-mEndFinder >= Twindow: #has there been no movement for 3 seconds?
                    if len(moves)==0:#if it's the first move, just slap that shit into moves
                        moves.append([round(mStart,2),mEndFinder,round(mEndFinder-mStart,2),round(mRunTot,2)])
                        mRunTot=0
                        
                    elif moves[-1][0] != mStart: #making sure that the line hasn't been added yet (for some reason it likes to add multiples of the same movement if I dont add this check)
                        if mRunTot>=move_threshold: #has the total movement been greater thanthe threshold? (done to minimize tiny moves that are meaningless)
                                #if yes, then slap it into moves
                            moves.append([round(mStart,2),mEndFinder,round(mEndFinder-mStart,2),round(mRunTot,2)])
                        #even if it HASNT been a greater than 2 yard move, clear mRunTot
                        mRunTot=0                   
    return(moves)

def get_boss_IDs(report):
    conn = http.client.HTTPSConnection("www.warcraftlogs.com")
    payload = str("{\"query\":\"{\\n    rateLimitData {limitPerHour pointsSpentThisHour pointsResetIn}\\n    reportData {\\n    report(code: \\\"")+str(report)+str("\\\"){ masterData{actors{name id gameID subType} \\n       }}}\\n\\n  \\n   \\n    }\\n    \\n\"}")
    headers = token
    conn.request("POST", "/api/v2", payload, headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    #print(data)
    #HORRIBLE EFFICIENCY, fix "later"
    names=['Shriekwing"','Huntsman Altimor"','Hungering Destroyer"','Lady Inerva Darkvein"','Sun King\'s Salvation"',"Artificer Xy\'mox\"",'Council of Blood"','Sludgefist"','Stone Legion Generals"','Sire Denathrius"']
    boss_npcIDs =    [[],[],[],[],[],[],[],[],[],[]]
    boss_local_IDs = [[],[],[],[],[],[],[],[],[],[]]
    b=data.split(',{"name":"')
    c=[]
    d=[]
    for k in b:
        c.append(k.split(','))
        #print(k)
    for i in c:
        if '"subType":"Boss"}' in i:
            d.append(i)
    for i in range (0,len(d)):
        if d[i][0] in names:
            boss_npcIDs[names.index(d[i][0])].append(d[i][1].strip('"id":'))
            boss_local_IDs[names.index(d[i][0])].append(d[i][2].strip('"gameID":'))
    return [boss_npcIDs,boss_local_IDs]


#THE ONE THAT ORCHASTRATES IT ALL
def data_parsing_handler(report):
    global start, end
    #determine the start/end time for that kill
    pick=str(boss_selected.get())+str('"')
    IDs=get_boss_IDs(report)
    boss_npcIDs,boss_local_IDs = IDs[0],IDs[1]
    #print(pick)
    #for i in names: print(i,pick)
    boss_npcID = boss_npcIDs[names.index(pick)][0]
    local_boss_id = boss_local_IDs[names.index(pick)][0]
    #print(boss_npcID,local_boss_id)
    stuff=get_start_end_EID(report,pick)
    #print(stuff)
    start=stuff[0]
    end=stuff[1]
   
    ENCOUNTER_ID = EIDtable[names.index(pick)]
    
    #print('boss_ID:',boss_ID,'ENCOUNTER_ID:',ENCOUNTER_ID, 'start:',start,'end:',end)
   
    #grab all the position data for that boss
    NPT,TXY=parse_position(report,start,end,boss_npcID,local_boss_id)[0],parse_position(report,start,end,boss_npcID,local_boss_id)[1]
    #print(output[0],NPT)
    #print(NPT)
    while NPT != 'null':
        #print('not null')
        #print('start was',start,'\n','NPT is',NPT, 'end =',end)
        ph=parse_position(report,NPT,end,boss_npcID,local_boss_id)
        NPT=ph[0]
        for i in ph[1]:
            TXY.append(i)
    return TXY


#takes the data from TXY, then converts it into a usable format (via TXY_to_TM), then slaps the data into the simcraft format
def parse_to_simc_handler(TXY):
    formated_moves=[] 
    moves=movement_intervals(TXY_to_TM(TXY))
    for i in moves:
        formated_moves.append(str("raid_events+=/movement,cooldown=9999,distance=")+str(i[3])+str(",duration=")+str(i[2])+str(",first=")+str(i[0]))
    return formated_moves
    

def drop_down_maker(creatureIDs):
    #print(creatureIDs)
    global boss_selected
    dd=[]
    for i in range (0,len(creatureIDs)):
        if len(creatureIDs[i])>0:
            dd.append(names[i].strip('"'))
    print(dd)
    boss_selected=StringVar(root)
    dropdown=OptionMenu(root,boss_selected,*dd)
    dropdown.pack()
    dropdown.place(x=10, y=50)
    
    encounterLabel = Label(root, text = "Select Encounter to parse")
    encounterLabel.pack()
    encounterLabel.place(x=0, y=30)
    
    bGO = Button(root,text ='Generate SimCraft Movement Script',command = GO)
    bGO.pack()
    bGO.place(x=300, y = 50)
    
    #return boss_selected


def grab_report_code():
    global report, local_IDs
    url=URL_entry.get()
    kek=url.split('https://www.warcraftlogs.com/reports/')
    topkek=kek[1].split('#')
    report=topkek[0]
    #print(report)
    local_IDs=get_boss_IDs(report)
    drop_down_maker(local_IDs[0])
    



    
def GO():
    boss_selected.get()
    TXY=data_parsing_handler(report)
    out=parse_to_simc_handler(TXY)
    T.delete(1.0,tk.END)
    for i in out:
        T.insert(tk.END, str(i)+str('\n'))
    




    #most fights have some additional non-random mechanics that meaningfully impact DPS that the simulation should deal with
def Enounter_specific_variances(boss,report):
    pass
    #obviously this is WIP
    








#########################################################################################################################################################
#########################################################################################################################################################
#########################################################################################################################################################
#########################################################################################################################################################
#########################################################################################################################################################
    
OUTPUT_TEXT = ''
root = Tk()
root.geometry('650x600')


T = Text(root, height = 30, width = 80) 
T.pack()
T.place(x=2, y=100)
T.insert(tk.END, OUTPUT_TEXT)

entrylabel=tk.Label(root, text="WCL Log URL:")
entrylabel.pack()
entrylabel.place(x=0,y=0)
#the entry box
URL_entry = tk.Entry(root,width=50)
URL_entry.pack()
URL_entry.place(x=80,y=1)

bGRAB = Button(root, text="Grab Log", command=grab_report_code)
bGRAB.pack()
bGRAB.place(x=385)






mainloop()
