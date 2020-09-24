# -*- coding: utf-8 -*-
"""
Created on Wed Sep 23 11:38:57 2020

@author: Daniel.Feeney
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import scipy.signal as sig
import seaborn as sns

# Define constants and options
fThresh = 50; #below this value will be set to 0.
writeData = 0; #will write to spreadsheet if 1 entered

# Read in balance file
fPath = 'C:/Users/Daniel.Feeney/Dropbox (Boa)/EnduranceProtocolWork/WalkData/'
entries = os.listdir(fPath)

# list of functions 
# finding landings on the force plate once the filtered force exceeds the force threshold
def findLandings(force):
    lic = []
    for step in range(len(force)-1):
        if force[step] == 0 and force[step + 1] >= fThresh:
            lic.append(step)
    return lic

#Find takeoff from FP when force goes from above thresh to 0
def findTakeoffs(force):
    lto = []
    for step in range(len(force)-1):
        if force[step] >= fThresh and force[step + 1] == 0:
            lto.append(step + 1)
    return lto

def trimLandings(landings, takeoffs):
    trimTakeoffs = landings
    if len(takeoffs) > len(landings) and takeoffs[0] > landings[0]:
        del(trimTakeoffs[0])
    return(trimTakeoffs)

def trimTakeoffs(landings, takeoffs):
    if len(takeoffs) < len(landings):
        del(landings[-1])
    return(landings)

#plt.plot(forceZ[landings[10]:landings[10]+1000])

#plt.plot(brakeFilt[landings[10]:landings[10]+1000])
#sum(brakeFilt[landings[10]+10:landings[10]+400])

def calcVLR(force, startVal, lengthFwd):
    # function to calculate VLR from 80 and 20% of the max value observed in the first n
    # indices (n defined by lengthFwd). 
    maxF = np.max(forceZ[startVal:startVal+lengthFwd])
    eightyPctMax = 0.8 * maxF
    twentyPctMax = 0.2 * maxF
    # find indices of 80 and 20 and calc loading rate as diff in force / diff in time (N/s)
    eightyIndex = next(x for x, val in enumerate(force[startVal:startVal+lengthFwd]) 
                      if val > eightyPctMax) 
    twentyIndex = next(x for x, val in enumerate(force[startVal:startVal+lengthFwd]) 
                      if val > twentyPctMax) 
    VLR = ((eightyPctMax - twentyPctMax) / ((eightyIndex/1000) - (twentyIndex/1000)))
    return(VLR)
    
#Find max braking force moving forward
def calcPeakBrake(force, landing, length):
    newForce = np.array(force)
    return min(newForce[landing:landing+length])

def findNextZero(force, length):
    # Starting at a landing, look forward (after first 15 indices)
    # to the find the next time the signal goes from - to +
    for step in range(length):
        if force[step] <= 0 and force[step + 1] >= 0 and step > 15:
            break
    return step

#Preallocation
loadingRate = []
peakBrakeF = []
brakeImpulse = []
VLR = []
VLRtwo = []
sName = []
tmpConfig = []

fName = entries[0]
## loop through the selected files
for file in entries:
    try:
        
        fName = file #Load one file at a time
        
        dat = pd.read_csv(fPath+fName,sep='\t', skiprows = 8, header = 0)
        #Parse file name into subject and configuration 
        subName = fName.split(sep = "_")[0]
        config = fName.split(sep = "_")[2]
        
        # Filter force
        forceZ = dat.RForceZ * -1
        forceZ[forceZ<fThresh] = 0
        brakeForce = dat.RForceY[0:59999] * -1
        
        
        fs = 1000 #Sampling rate
        t = np.arange(59999) / fs
        fc = 20  # Cut-off frequency of the filter
        w = fc / (fs / 2) # Normalize the frequency
        b, a = sig.butter(4, w, 'low')
        brakeFilt = sig.filtfilt(b, a, brakeForce)
        
        #find the landings and offs of the FP as vectors
        landings = findLandings(forceZ)
        takeoffs = findTakeoffs(forceZ)
                
        ### end test ###
        
        #For each landing, calculate rolling averages and time to stabilize
    
        for landing in landings:
            try:
                sName.append(subName)
                tmpConfig.append(config)
                peakBrakeF.append(calcPeakBrake(brakeFilt,landing, 600))
                # Define where next zero is
                nextLanding = findNextZero(brakeFilt,600)
                brakeImpulse.append(sum(brakeFilt[landing+10:landing+nextLanding]))
                VLR.append(calcVLR(forceZ, landing, 200))
            except:
                print(landing)
        
    except:
            print(file)

outcomes = pd.DataFrame({'Sub':list(sName), 'Config': list(tmpConfig), 'peakBrake': list(peakBrakeF),
                         'brakeImpulse': list(brakeImpulse), 'VLR': list(VLR)})

outcomes[['peakBrake']] = -1 * outcomes[['peakBrake']]
    
ax = sns.boxplot(y='peakBrake', x='Sub', hue="Config",
                 data=outcomes, 
                 palette="colorblind")
ax.set(xlabel='Condition', ylabel='Braking Force')

ax2 = sns.boxplot(y='VLR', x='Sub', hue = "Config", 
                 data=outcomes, 
                 palette="colorblind")
ax2.set(xlabel='Condition', ylabel='VLR')

ax3 = sns.boxplot(y='brakeImpulse', x='Sub', hue = "Config", 
                 data=outcomes, 
                 palette="colorblind")
ax3.set(xlabel='Condition', ylabel='brakeImpulse')