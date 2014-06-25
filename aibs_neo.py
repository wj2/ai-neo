# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 11:54:37 2014

@author: djd
"""

import numpy as np
import quantities as pq
import neo
import cPickle as pkl


#input is a path to a .pkl
#output is a neo Block
def pklToBlock(path):
    data = pkl.load(open(path))
   
   #create the block
    blk = neo.Block()
    
    #choose the segment organization, right now done by laps, because that's the only loader i've written...
    blk.segments.append(createLapSegments_behavior(data))
    blk.annotate(data = convertStairsToDict(data))
    return blk

#input is a neo Block, start and end are Segment list indices
#output is a neo Block
def block_subset(inpt,(start,end)):
    outStructure = neo.Block()
    outStructure.segments.append(inpt.segments[0][start:end])
    outStructure.annotate(data=inpt.annotations['data'])

#input is a neo Block
#output is data structure compatible with the Performance Viewer
def blockToAIBS(inpt):
    
    #get the original data structure    
    data = inpt.annotations['data']
    
    #replace the parts that are variable over the session with
    #the parts from just the desired subset of the session:
    for i,segment in inpt.segments:
#        data['bgSweepFrames']=
#        data['dx']=
#        data['intervalsms']=
#        data['laps']=
#        data['lickData']=
#        data['posx']=
#        data['reward']=
#        data['terrainlog']=
#        data['terrainlog_secondstream']=
#        data['vin']=
#        data['vsig']=
#        data['vsyncintervals']=
        a=1
    #return results    
    return data

def convertStairsToDict(data):
    stairs  = data['staircase'].__dict__
    data['staircase'] = stairs
    return data
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
def createLapSegments_behavior(data,**kwargs):
    #create a neo segment for each lap, with appropriate metadata
    if 'clock' in kwargs.keys():
        clock = kwargs['clock']
        #sync specified clock to vstim
        if clock=='vstim':
            time =  computeUpdateTimes(data['vsyncintervals'])
        else:
            #output a time array that has the same number of frames as vsyncs, but in the specifiec timebase as opposed to vsync intervals
            time = np.array(1);
    else:
        clock = 'vstim'
        time =  computeUpdateTimes(data['vsyncintervals'])
        
    segmnts= neo.Block()
    for i in range(len(data['terrainlog'])-1):#don't look at the last entry, as it was a lap started but not completed.
        s = neo.Segment(index=i,name=''.join(('lap ',str(i+1))),rec_datetime=data['startdatetime'])

        #compute some things for this lap
        lapstart, lapend = getLapIndex(data,encounterindex=i)
        t = np.array(time[lapstart:lapend])/1000.0 #convert to seconds
        x = np.array(data['posx'][lapstart:lapend])
        v = np.array(data['dx'][lapstart:lapend])/t
        a = v/t 
        
        #reward and stopping
        rewarded = getRewardInfo(data,t[0],t[len(t)-1])
        pauseTime = getPauseTime(x,t,data,i)
        isCorrect = getResponse(data,i,pauseTime)
        
        #licking
        if len(data['lickData']) > 1:
            lick=True
            licks= getLicksTrial(data['lickData'],lapstart, lapend)
        
        #eye tracking
        if data['params']['eyetracker']:
            eyeX,eyeY = getEyeTraces(data['eyetrackerreport'])

        #optogenetics
        if data['optogenetics']:
            optoTrial = False#get whether or not this was an optoTrial
            optoTrace = np.zeros(10)#continuous representation of when the LED was on
            optoColor = 'blue'#where is this info in the data?

        #djd: add a quantities pixel unit here. need to know screen size and viewing distance
            #pix = pq.UnitQuantity('pixel',screenWidth*pq.meter/xPixels,symbol=''pix')
        
        #******************************************************************************
        #store metadata
        s.annotate(task=data['task']);
        s.annotate(terrain=data['terrainlog'][i])
        #s.annotate(stimulus=data['terrainlog'][i])
        s.annotate(terrain_second=data['terrainlog_secondstream'][i])
        s.annotate(starttime=time[lapstart]/1000) #convert to seconds
        s.annotate(reward=rewarded)
        s.annotate(pauseTime=pauseTime)
        s.annotate(correct=isCorrect)
        #selection time on this lap, other format of stim information, how to deal with staircase parameters?
        #******************************************************************************
        
        #******************************************************************************
        #store analog signals
        s.analogsignals.append(neo.AnalogSignal(x,sampling_rate=data['fps']*pq.Hz,units=pq.meter,name='x'))
        s.analogsignals.append(neo.AnalogSignal(t,sampling_rate=data['fps']*pq.Hz,units=pq.second,name='t'))
        s.analogsignals.append(neo.AnalogSignal(v,sampling_rate=data['fps']*pq.Hz,units=pq.meter/pq.second,name='v'))
        s.analogsignals.append(neo.AnalogSignal(a,sampling_rate=data['fps']*pq.Hz,units=pq.meter/(pq.second*pq.second),name='a'))
        #s.analogsignals.append(neo.AnalogSignal(vin,sampling_rate=data['fps'],name='vin'))     
        #s.analogsignals.append(neo.AnalogSignal(intervalsms,sampling_rate=data['fps'],name='intervalsms'))     
        #s.analogsignals.append(neo.AnalogSignal(vsig,sampling_rate=data['fps'],name='vsig'))     
        #s.analogsignals.append(neo.AnalogSignal(vsyncintervals,sampling_rate=data['fps'],name='vsyncintervals'))     
        if data['params']['eyetracker']:
            s.analogsignals.append(neo.AnalogSignal(eyeX,sampling_rate=data['fps']*pq.Hz,units=pq.meter))
            s.analogsignals.append(neo.AnalogSignal(eyeY,sampling_rate=data['fps']*pq.Hz,units=pq.meter))
        #******************************************************************************
        
        #******************************************************************************
        #spike trains
        if lick:
            s.spiketrains.append(neo.SpikeTrain(licks/1000,units='sec',t_stop=lapend/1000))        
        #******************************************************************************
        
        segmnts.segments.append(s)
    #segmnts.annotate(data=data)
    return segmnts

def computeUpdateTimes(vsyncintervals):
        t = [0]
        for i,v in enumerate(vsyncintervals):
            t.append((t[i]+v))        
        t.append(np.nan)#add one to balance
        return t
def getEyeTraces(eyedata):
    eyeX=2
    eyeY=2    
    return eyeX,eyeY
def getLapIndex(data,encounterindex = 0):
    if encounterindex == 0:
        lapstart = 0
    else:
        lapstart = data['laps'][encounterindex-1][1]
    if encounterindex == len(data['laps'])-1:
        lapend = len(data['posx'])
    else:
        lapend = data['laps'][encounterindex][1]
    return int(lapstart), int(lapend)
        
def getRewardInfo(data,lapstart,lapend):
    rewarded = False
    for i in range(np.shape(data['rewards'])[0]):
        if data['rewards'][i][0] > lapstart and data['rewards'][i][0] < lapend:
            rewarded = True
            return rewarded
    return rewarded

def getResponse(data,i,pauseTime):  
    report = data['behavioralreport']
    if report == 'stopping':
        selectionTime = getTerrainParameterLap(data,'selectiontime',i)#data['terrain']['selectiontime']
        if pauseTime > selectionTime:
            return True
        else:
            return False
    if report == 'licking':
        return False

def getPauseTime(x,t,data,lap):#stolen from ForageSession.py by shawn and doug
    x = np.array(x)
    t = np.array(t)
    winx = getTerrainParameterLap(data,'windowx',lap);
    winwidth = getTerrainParameterLap(data,'windowwidth',lap)
    rw = [winx-winwidth, winx+winwidth]   
    in_rw = np.logical_and(x >= rw[0], x < rw[1]) 
    crossing = np.diff(in_rw)
    idx = crossing.nonzero()[0] 
    if len(idx) != 0:
        idx += 1
        if in_rw[0]:
            # If the start of condition is True prepend a 0
            idx = np.r_[0, idx]
        if in_rw[-1]:
            # If the end of condition is True, append the length of the array
            idx = np.r_[idx, in_rw.size] # Edit
        idx.shape = (-1,2)
        # Find index of max contiguous region (if multple, first occurrence returned)
        imax = np.argmax(np.diff(idx))
        pauseInd = idx[imax];
        if pauseInd[1] < len(t)-1:
            pauseTime = t[pauseInd[1]+1] - t[pauseInd[0]]
        else:
            pauseTime = np.nan
        return pauseTime
    else:
        return np.nan
                
def getTerrainParameterLap(data,param,lap):
    if data['adaptivestaircase']:
        if data['staircase'].parameter == ''.join(('terrain.',param)):
            return data['staircase'].log[lap]
        else:
            return data['terrain'][param]    
    else:
        return data['terrain'][param]
        
def getLicksTrial(lickData,lapstart, lapend):
    startIndex = -1; endIndex = -1;
    for i in range(np.shape(lickData[0])[0]):
        if lickData[0][i] > lapstart and startIndex < 0:
            startIndex=i
        if lickData[0][i] > lapend and endIndex < 0:
            endIndex=i-1
    return lickData[0][startIndex:endIndex]
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------



        
    
    















         
def createBackgroundSegments_behavior(data,**kwargs):
    #create a neo segment for each background stimulus, with appropriate metadata
    if 'clock' in kwargs.keys():
        clock = kwargs['clock']
        #sync specified clock to vstim
    else:
        clock = 'vstim'
        
    segments = []
    for i in range(len(data['bgsweeptable'])):
        s = neo.Segment(index=i,name=''.join(('sweep',str(i))),rec_datetime=data['startdatetime'])
        
        segments[i]=s
        
    return segments
    
def createTrialSegments_2P(data,**kwargs):
    if 'clock' in kwargs.keys():
        clock = kwargs['clock']
        #sync specified clock to vstim
    else:
        clock = 'vstim'
        
def createTrialSegments_widefield(data,**kwargs):
    if 'clock' in kwargs.keys():
        clock = kwargs['clock']
        #sync specified clock to vstim
    else:
        clock = 'vstim'
        
def createTrialSegments_ephys(data,**kwargs):       
    if 'clock' in kwargs.keys():
        clock = kwargs['clock']
        #sync specified clock to vstim
    else:
        clock = 'vstim'

        
        
if __name__ == "__main__":
    block =  neo.Block()