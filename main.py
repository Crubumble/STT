# -*- coding: utf-8 -*-
"""
This programm will provide a first analyses of your crew for voyages.

OPEN steps:
1. Fill crew table with more crew and the fuse stages
2. Improve anaylses by showing the impact of fusing a char
3. Improve sample function
    3.1 Code usage
    3.2 Improve algorithm by user intel

TODO improve runtime
search doubles or double use 

Fehler bei SEC COM im vergelich zu alter version drop from 8.5 to 8 h




"""
import pandas as pd
import numpy as np
import pickle
import sys
import os
import math
from openpyxl import Workbook


# default values
ALIN = 0.314         # dif/sec linear increase
GSP = 94       # challenge each x seconds
WGAIN = 5       # gain 5 anti matter
LGAIN = -30
GST = 26       # standard challenge every y sec
YSTART = 500   # difficulty at time t = 0 sec
CHANGER = 0.1   # if INICHANGE make time worse reduce the factor with this less
INICHANGE = 0.5  # reduce the multiplication factor for the prim and sec att
LOOPS = 100  # in case of an infinity loop exit counter


def gotBot(time, sample, AM_ini):  # estimate the time of the voyage
    sample = sample - YSTART
    sample[sample < 0] = 0
    t_frac = sample/(ALIN * time)
    opti = t_frac > 1.1
    t_frac[t_frac > 1] = 1
    share = np.array([0.35, 0.25, 0.1, 0.1, 0.1, 0.1])
    w_sp = (t_frac * share).sum()
    return opti, float(AM_ini - time/GST + WGAIN * math.ceil(w_sp * time/GSP) + LGAIN * int((1-w_sp) * time/GSP))


def esti_time(sample, AM=2500, time=28801.0):
    opti, rem_AM = gotBot(time, sample, AM)
    estimator = (1/(-1/GST+1/GSP*LGAIN))  # estimate that last are all fails
    if abs(rem_AM) > 40:
        time -= rem_AM * estimator  # with this assumtion no recression needed
        esti_time(sample, AM, time)
    return time, opti


def initialCrew(prim, sec, pfac=3.5, sfac=2.5):
    # print('prime is %s and second is %s' % (prim, sec))
    df_Crew = pickle.load(open('staff.p', 'rb'))
    df_Values = df_Crew.copy()
    # multiple first
    df_Values[prim] = df_Values[prim].mul(pfac)
    df_Values[sec] = df_Values[sec].mul(sfac)
    minor = pd.Series(df_Crew.columns)
    # pick the other attribute first
    df_slct = pd.DataFrame(columns=['Att'])
    for att in minor:
        df_slct = df_slct.append(df_Values[df_Values[att] > 0].
                                 sum(axis=1).sort_values(ascending=False).
                                 reset_index()[:12])
        df_slct = df_slct.fillna(att)
    df_slct.reset_index(inplace=True)
    df_slct.columns = ['Rank', 'Att', 'Name', 'Value']
    # pick the five best charaters
    df_voy = df_slct.loc[df_slct.Rank < 2, ('Att', 'Name')]
    return df_voy, df_slct


def getSample(prim, sec, df_voy, df_slct):  # returns Crew for Voyage
    if df_voy.Name.duplicated().any():
        for char in df_voy[df_voy.Name.duplicated()].Name.unique():
            reserve = pd.DataFrame(columns=df_slct.columns)
            change = pd.DataFrame(columns=df_slct.columns)
            for att in df_voy.loc[df_voy.Name == char, 'Att']:
                reserve = reserve.append(df_slct.loc[df_slct.Att == att][df_slct.loc[df_slct.Att == att].Name.isin(df_voy.Name) == False].iloc[0:2])
                change  = change.append(df_slct.loc[df_slct.Att == att][df_slct.loc[df_slct.Att == att].Name.isin(df_voy.Name) == False].iloc[0:2])           
            reserve.sort_values(by='Value', ascending=False, inplace=True)
            from itertools import cycle
            seq = cycle([1, 2])
            change['Rank'] = [next(seq) for count in range(change.shape[0])]
            change.reset_index(drop=True, inplace=True)
            num_use = len(change.Att.unique())  # number used in inital selection
            if len(change.loc[change.Rank == 1].Name.unique()) == num_use:
                # all alternatives are different
                if num_use == 2:
                     #pick max Value as the alternative right away
                    newName = change.loc[change.Value == max(change.Value)].Name.iloc[0]
                    chaAtt = change.loc[change.Value == max(change.Value)].Att.iloc[0]
                    df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt), 'Name'] = newName                   
                else:
                     #remain att with lowest alternative max Value as the alternative right away
                    a = np.array(change.Att.unique(), dtype=np.str)
                    keep = change[change.Value == min(change.loc[change.Rank == 1, 'Value'])].Att.iloc[0]
                    chaAtt = np.array(a[a != keep], dtype=str)
                    df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt[0]), 'Name'] = change.loc[(change.Rank == 1) & (change.Att == chaAtt[0])].Name.iloc[0]
                    df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt[1]), 'Name'] = change.loc[(change.Rank == 1) & (change.Att == chaAtt[1])].Name.iloc[0]                                    
            elif num_use == 2:
                # check Rank 2
                if len(change.loc[change.Rank == 2].Name.unique()) == num_use:
                    # replace the char with higher value for Rank 2 with char from Rank 1, since the other keeps the original (highest) value
                    newName = change.loc[change.Value == max(change.Value)].Name.iloc[0]
                    chaAtt = change.loc[change.Value == max(change.loc[change.Rank == 2].Value), 'Att'].iloc[0]
                    df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt), 'Name'] = newName
                else:
                    # all the same = it doesnt matter
                    newName = change.loc[change.Value == max(change.Value)].Name.iloc[0]
                    chaAtt = change.loc[change.Value == max(change.Value)].Att.iloc[0]
                    df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt), 'Name'] = newName
            else:
                # char is used three times (more not possible)
                # find second best choice for each att
                if (len(change.loc[change.Rank == 1].Name.unique()) == 1) and (len(change.loc[change.Rank == 2].Name.unique()) == 1):
                    # order irrelevant
                    df_voy.loc[(df_voy.Name == char) & (df_voy.Att == str(change.Att.iloc[0])), 'Name'] = change.Name.iloc[0]
                    df_voy.loc[(df_voy.Name == char) & (df_voy.Att == str(change.Att.iloc[2])), 'Name'] = change.Name.iloc[1]
                    # df_voy.loc[(df_voy.Name == char) & (df_voy.Att == str(change.Att.iloc[6])), 'Name'] = change.Name.iloc[2]
                elif (len(change.loc[change.Rank == 1].Name.unique()) == 1):
                    # second alternative determines one att to be choosen for the char.
                    a = np.array(change.Att.unique(), dtype=np.str)
                    keep = change[change.Value == min(change.loc[change.Rank == 2, 'Value'])].Att.iloc[0]
                    chaAtt = np.array(a[a != keep], dtype=str)
                    if len(change.loc[change.Rank == 2].Name.unique()) == 2:
                        # two choices are the same for the second alternative
                        df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt[0]), 'Name'] = change.loc[(change.Rank == 1) & (change.Att == chaAtt[0])].Name.iloc[0]
                        df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt[1]), 'Name'] = change.loc[(change.Rank == 2) & (change.Att == chaAtt[1])].Name.iloc[0]                   
                    else:
                        # all second choice are different
                        keep = change[change.Value == max(change.loc[change.Rank == 2, 'Value'])].Att.iloc[0]  # take the second alternative
                        chaAtt = str(chaAtt[chaAtt != keep][0])
                        df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt), 'Name'] = change.loc[(change.Rank == 1) & (change.Att == chaAtt)].Name.iloc[0] # take the first alternative
                        df_voy.loc[(df_voy.Name == char) & (df_voy.Att == keep), 'Name'] = change.loc[(change.Rank == 2) & (change.Att == keep)].Name.iloc[0] # take the second alternative
                elif (len(change.loc[change.Rank == 1].Name.unique()) == 2):
                    # thrChoice determine one att to be choosen for the char.
                    a = np.array(change.Att.unique(), dtype=np.str)
                    keep = change[change.Value == min(change.loc[change.Rank == 1, 'Value'])].Att.iloc[0]
                    chaAtt = np.array(a[a != keep], dtype=str)
                    if len(change.loc[change.Rank == 2].Name.unique()) == 2:
                        # two choices are the same for the second alternative
                        df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt[0]), 'Name'] = change.loc[(change.Rank == 1) & (change.Att == chaAtt[0])].Name.iloc[0]
                        df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt[1]), 'Name'] = change.loc[(change.Rank == 2) & (change.Att == chaAtt[1])].Name.iloc[0]                   
                    else:
                        # all second choice are different
                        keep = change[change.Value == max(change.loc[change.Rank == 2, 'Value'])].Att.iloc[0]  # take the second alternative for that attribute
                        chaAtt = str(chaAtt[chaAtt != keep][0])
                        df_voy.loc[(df_voy.Name == char) & (df_voy.Att == chaAtt), 'Name'] = change.loc[(change.Rank == 1) & (change.Att == chaAtt)].Name.iloc[0] # take the first alternative
                        df_voy.loc[(df_voy.Name == char) & (df_voy.Att == keep), 'Name'] = change.loc[(change.Rank == 2) & (change.Att == keep)].Name.iloc[0] # take the second alternative               
    df_voy.reset_index(drop=True, inplace=True)
    return df_voy


def AnalyseCrew(Anti=2650, filename='example.xls'):
    # get all combinations of att and list die chars as well as the time
    import itertools
    df_Crew = pickle.load(open('staff.p', 'rb'))
    df_summary = pd.DataFrame(columns=['Primary', 'Secondary', 'Time', 'COM1',
                                       'COM2', 'DIP1', 'DIP2', 'ENG1', 'ENG2',
                                       'MED1', 'MED2', 'SEC1', 'SEC2', 'SIC1',
                                       'SIC2'], dtype=np.str0)
    df_summary = df_summary.astype({u'Time': np.float})
    allchallenges = list(itertools.permutations(df_Crew.columns, 2))
    freqNames = ['']
    for a in allchallenges:
        df, time, sample = getVoyageCrew(prim=a[0], sec=a[1], Anti=Anti, filename=filename)
        freqNames.extend(df.Name.tolist())
        df_summary.loc[len(df_summary), 'Primary'] = a[0]
        df_summary.loc[len(df_summary)-1, 'Secondary'] = a[1]
        df_summary.loc[len(df_summary)-1, 'Time'] = round(time / 3600.0, 3)
        df_summary.iloc[len(df_summary)-1, 3:] = df.Name.tolist()
    # give an overview about how often each crew member is used
    df_freq = pd.DataFrame(freqNames, columns=['Char'])
    df_freq = df_freq.groupby(df_freq.columns.tolist()).size().reset_index().rename(columns={0:'count'})    
    df_freq.sort_values(by='count', ascending=False, inplace=True)
    df_freq.reset_index(drop=True, inplace=True)
    del freqNames
    df_chars = pd.read_excel(filename, sheetname='Stats', header=[1], usecols = [0,1,2,3]).fillna('o')
    df_chars = df_chars[df_chars.iloc[:, 3] == 'x']
    # use df_Crew to loo if one of them can be further improved and which att is your weak spot
    print('Useless crew for voyage %s :' % df_chars[df_chars.Name.isin(df_freq.Char) == False].Name.tolist())
    print('Crew you should fuse:\n %s ' % df_freq.loc[df_freq.Char.isin(df_chars[df_chars.Name.isin(df_freq.Char) & (df_chars.Having != df_chars.Maximum)].Name)])
    return df_summary, df_freq


def setCrew(filename):  # get Data from your Crew
    #  read in Data
    df_chars = pd.read_excel(filename, sheetname='Stats', header=[0, 1])
    # skip_footer=5).transpose().reset_index().sort_values(by=['level_0', 'Name']).reset_index(drop=True).fillna(0)
    df_chars = df_chars[df_chars.iloc[:, 2] == 'x']
    df_chars = df_chars.transpose().reset_index().sort_values(by=['level_0', 'Name']).reset_index(drop=True).fillna(0)
    df_chars.drop(df_chars.tail(3).index, inplace=True)
    df_chars.rename(columns={'level_0': 'Skill',
                             'Name': 'Type'}, inplace=True)
    df_chars.iloc[:, 2:] = df_chars.iloc[:, 2:].astype(float)
    #  Adjust the values from the char database with your boni
    df_BoniBase = pd.read_excel(filename, sheetname='Bonus_Base', header=[0]).transpose()
    df_BoniOwn = pd.read_excel(filename, sheetname='Bonus_Own', header=[0]).transpose()
    df_bonus = df_BoniBase + df_BoniOwn
    df_bonus.columns = df_bonus.iloc[0]
    df_bonus = df_bonus.drop('Attribute').stack().reset_index().sort_values(by=['level_0', 'Attribute']).reset_index(drop=True)
    df_bonus.columns = ['Skill', 'Type', 'Value']
    df_bonus.Value += 1
    df_chars.iloc[:, 2:] = df_chars.iloc[:, 2:].mul(df_bonus['Value'], axis=0)
    #  Building the single value for voyage
    df_charValues = pd.DataFrame(columns=df_chars.Skill.unique())
    for att in df_chars.Skill.unique():
        df_charValues[att] = df_chars.iloc[:, 2:].loc[(df_chars.Skill == att)
        & (df_chars.Type.str.contains('M'))].sum().mul(0.5)
    df_state = df_chars.loc[df_chars.Type == 'State'].T
    df_state.columns = df_state.iloc[0]
    df_state.drop(['Skill', 'Type'], inplace=True)
    df_charValues = df_charValues.add(df_state)
    df_charValues = df_charValues.astype(np.float).apply(np.ceil)  # roundingUP
    pickle.dump(df_charValues, open('staff.p', 'wb'))


def buildSample(df_voy, prim, sec):
    # Build sample
    df_Crew = pickle.load(open('staff.p', 'rb'))
    sample = df_Crew[df_Crew.index.isin(df_voy.Name)].sum()
    vPrim = sample[prim]
    vScd = sample[sec]
    del sample[prim]
    del sample[sec]
    sample_start = np.array([vPrim, vScd])
    return np.concatenate((sample_start, sample))


def getVoyageCrew(prim='SEC', sec='SIC', Anti=2650,
                  filename='example.xls',
                  pfac=3.5, sfac=2.5):
    df_voy, time, sample, opti = optimizer(prim=prim, sec=sec, Anti=Anti,
                                           pfac=3.5, sfac=2.5)
    pfac_changer = INICHANGE
    sfac_changer = INICHANGE
    changer = False
    opti_old = opti
    counter = 0
    binfo = True
    while (opti.any()):
        time_old = time
        if opti[0]:
            if changer:
                pfac += pfac_changer
                pfac_changer = pfac_changer - CHANGER
            else:
                pfac -= pfac_changer
            # sfac += 0.05
        if opti[1]:
            if changer:
                sfac += sfac_changer
                sfac_changer = sfac_changer - CHANGER
            else:
                sfac -= sfac_changer
        if not opti[0:2].any():
            print('prim %s and sec %s are optimized. '
                  'Further att increasing. ' % (prim, sec))
            break
        else:
            changer = False
            df_voy, time, sample, opti = optimizer(prim=prim, sec=sec,
                                                   Anti=Anti,
                                                   pfac=pfac, sfac=sfac)
            # print(prim, sec, time_old, time, pfac, sfac, pfac_changer, sfac_changer)
            if counter > LOOP:
                print('Endless loop for %s and %s detected.' % (prim, sec))
                break
            if time < time_old - 300:
                opti = opti_old
                changer = True
            else:
                opti_old = opti
                if np.isclose(pfac_changer, 0) | np.isclose(sfac_changer, 0):
                    # print('Optimum achieved')
                    break
                counter += 1
            if (sfac < 1.0) | (pfac < 1.0):
                if binfo:
                    print('prim %s or sec %s very strong compared to other values' %(prim, sec))
                    binfo = False
    return df_voy, time, sample


def optimizer(prim='SEC', sec='SIC', Anti=2650,
              pfac=3.5, sfac=2.5):
    df_voy, df_slct = initialCrew(prim, sec, pfac, sfac)
    # df_voy = getSample(prim, sec, df_voy, df_slct)
    if len(df_voy) == 0:
        print('ERROR. Crew selection is empty!')
        sys.exit()
    c = 0
    while (len(df_voy.Name.unique()) != len(df_voy.Name)) & (c < 5):
        df_voy = getSample(prim, sec, df_voy, df_slct)
        c += 1
        # print('Alternatives used more than once for %s and %s' % (prim, sec))
    sample = buildSample(df_voy, prim, sec)
    time, opti = esti_time(sample, Anti)
    return df_voy, time, sample, opti


def config():
    # set variables
    config = 'config.txt'
    if config not in os.listdir(os.getcwd()):
        print('%s not in directory, default values used.' % config)
        return
    f = open('config.txt')
    data = f.readlines()
    f.close()
    global ALIN    # dif/sec linear increase
    global GSP     # challenge each x seconds
    global WGAIN   # gain 5 anti matter
    global LGAIN
    global GST     # standard challenge every y sec
    global YSTART  # difficulty at time t = 0 sec
    global CHANGER  # adjustment of factor reducement
    global INICHANGE
    global LOOP
    for n, line in enumerate(data, 1):
        if 'ALIN' in line:
            ALIN = float(line.split()[2])
        elif 'GSP' in line:
            GSP = int(line.split()[2])
        elif 'WGAIN' in line:
            WGAIN = int(line.split()[2])
        elif 'LGAIN' in line:
            LGAIN = int(line.split()[2])
        elif 'GST' in line:
            GST = int(line.split()[2])
        elif 'YSTART' in line:
            YSTART = int(line.split()[2])
        elif 'CHANGER' in line:
            CHANGER = float(line.split()[2])
        elif 'INICHANGE' in line:
            INICHANGE = float(line.split()[2])
        elif 'LOOP' in line:
            LOOP = float(line.split()[2])
    #return ALIN, GSP, WGAIN, LGAIN, GST, YSTART, CHANGER


if __name__ == '__main__':
    config()
    while True:
        entered = input("Please choose if you want to analyse your crew "
                        "for all possible voyages or just find the best "
                        "crew for a specific run [Analyses or Voyage] \n"
                        "Exit with empty input [ENTER]\n")
        if not entered:
            break
        if entered in ['Analyses', 'Voyage']:
            anti_para = input('Amount of anti matter? ')
            try:
                anti_para = int(anti_para)
                fn = input('Great. Last question. Do you want to update '
                           'your crewtable? If yes, please enter the '
                           'filename. Otherwise staff.p will be used. '
                           'In that case press ENTER \n')
                if not fn:
                    if 'staff.p' not in os.listdir(os.getcwd()):
                        fn = 'example.xls'
                        setCrew(fn)
                elif fn not in os.listdir(os.getcwd()):
                    print('Sorry. %r not in this folder' % fn)
                    continue
                else:
                    setCrew(fn)
            except ValueError:
                print('Anti %i mater must be an integer.' % anti_para)
                continue
            if entered == 'Analyses':
                df_summary, df = AnalyseCrew(Anti=anti_para,
                                             filename='example.xls')
                print('Overview are printed out to Analyser.xlsx')
                writer = pd.ExcelWriter('Analyser.xlsx', engine='openpyxl')
                writer.book = book = Workbook()
                df_summary.to_excel(writer, sheet_name='Summary',
                                    startrow=1, index=False)
                df.to_excel(writer, sheet_name='Crew_Usage',
                            startrow=1, index=False)
                writer.save()
                writer.close()
                break
            else:
                prim = input('Well. Really last question. Please set primary '
                             'and secondary attribute \n'
                             'Choose from [COM, DIP, SEC, SIC, ENG, MED] \n'
                             'Please enter your primary attribute \n')
                if not str.upper(prim) in ['COM', 'DIP', 'SEC', 'SIC',
                                           'ENG', 'MED']:
                    print('Sorry please choose from [COM, DIP, SEC, SIC,'
                          'ENG, MED]')
                    continue
                sec = input('Please enter your secondary attribute \n')
                if not str.upper(sec) in ['COM', 'DIP', 'SEC', 'SIC',
                                          'ENG', 'MED']:
                    print('Sorry please choose from [COM, DIP, SEC, '
                          'SIC, ENG, MED]')
                    continue
                df_voy, time, sample = getVoyageCrew(prim=str.upper(prim),
                                                     sec=str.upper(sec),
                                                     Anti=anti_para,
                                                     filename=fn)
                time = time / 3600.0
                hours = int(time)
                minutes = int(round(((time % 1) * 60), 0))
                yotime = str('%s h and %s min' % (hours, minutes))
                print('Your voyage lasts %s' % yotime)
                print('Sample is %s' % sample)
                print(df_voy)
                break
        else:
            print("%r is NOT equal Analyses or Voyage. "
                  "Please also use inital capitals!" % entered)
            continue
    input('Program ends with any key and press ENTER')
