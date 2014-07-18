# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 11:54:37 2014

@author: djd
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 11:54:37 2014

@author: djd
"""
import os
import tkFileDialog
import numpy as np
import quantities as pq
import neo
import cPickle as pkl
import pandas as pn


#TODO djd:class? that incorporates all of this, including pandas
class AIBSBlock(object):
    def __init__(self,**kwargs):
        #block = pklToBlock(path):
        #ff = pn.DataFrame(block)
        if 'path' in kwargs.keys():
            self.path = kwargs['path']  
        else:
            self.path = tkFileDialog.askopenfilename();
            
        self.block = self.pklToBlk(self.path)
        self.ff = self.createFFfromBlock(self.block)

    #------------------------------------------------------------------------------
    #behavior I/O: in------------------------------------------------------------------
    #------------------------------------------------------------------------------
    #input is a path to a .pkl
    #output is a neo Block
    def pklToBlock(path):
        data = pkl.load(open(path))
       
       #create the block
        blk = neo.Block()
        
        #choose the segment organization, right now done by laps, because that's the only loader i've written...
        blk=createLapSegments_behavior(data)
        if data['adaptivestaircase']:
            blk.annotate(data = convertStairsToDict(data))
        else:
            blk.annotate(data = data)
        return blk
    #------------------------------------------------------------------------------
    def createFFfromBlock(block):
        ff = pn.DataFrame()
        #TODO: djd: populate the data frame with forage information
        return ff
                
#------------------------------------------------------------------------------
#input is a neo Block, start and end are Segment list indices
#output is a neo Block
def block_subset(inpt,(start,end)):
    outStructure = neo.Block()
    outStructure.annotations=inpt.annotations
    for i in range(abs(end-start)+1):
        outStructure.segments.append(inpt.segments[i])
    return outStructure
#------------------------------------------------------------------------------
    
#------------------------------------------------------------------------------    
#input is a neo Block
#output is data structure compatible with the Performance Viewer
#
def blockToPkl(inpt,path,**kwargs):
    
    #get the original data structure 
    #and parse the name of the to be saved pkl, iterating if one of the same name already exists
    data = inpt.annotations['data']
    if 'name' in kwargs.keys():
        name = name =''.join((data['stopdatetime'].split(' ')[0].replace('20','').replace('-',''),data['stopdatetime'].split(' ')[1].split('.')[0].replace('-','').replace(':',''),'-',data['startdatetime'].split(' ')[0].replace('20','').replace('-',''),data['startdatetime'].split(' ')[1].split('.')[0].replace('-','').replace(':',''),'-',data['mouseid'],'-',kwargs['name'],'.pkl'))
    else:
        name =''.join((data['stopdatetime'].split(' ')[0].replace('20','').replace('-',''),data['stopdatetime'].split(' ')[1].split('.')[0].replace('-','').replace(':',''),'-',data['startdatetime'].split(' ')[0].replace('20','').replace('-',''),data['startdatetime'].split(' ')[1].split('.')[0].replace('-','').replace(':',''),'-',data['mouseid'],'.pkl'))
        if name in os.listdir(path):
            name = ''.join((data['stopdatetime'].split(' ')[0].replace('20','').replace('-',''),data['stopdatetime'].split(' ')[1].split('.')[0].replace('-','').replace(':',''),'-',data['startdatetime'].split(' ')[0].replace('20','').replace('-',''),data['startdatetime'].split(' ')[1].split('.')[0].replace('-','').replace(':',''),'-',data['mouseid'],'-',str(os.listdir(path).count(name)),'.pkl'))
   
   #replace the parts that are variable over the session with
    #the parts from just the desired subset of the session:
    data['laps']= np.zeros((len(inpt.segments),2))
    data['rewards']=np.zeros((len(inpt.segments),3))
    if len(data['lickData']) > 1:
        lick=True
        #data['lickData']=([],[])
    else:
        lick=False
    for i in range(len(inpt.segments)):
        segment = inpt.segments[i]
        if i==0:
            #data['bgSweepFrames']=segment.analogsignals[8]
            data['dx']=np.array(segment.analogsignals[2]*segment.analogsignals[1]).astype(float);data['dx'][0]=0
            data['intervalsms']=np.array(segment.analogsignals[5])
            data['laps'][0,0]= segment.annotations['endtime']+data['starttime'];data['laps'][0,1]= segment.annotations['endframe']
            if lick:
                data['lickData']=np.array(segment.spiketrains[0].times)
            data['posx']=np.array(segment.analogsignals[0])
            if segment.annotations['rewarded']:
                data['rewards'][i,0]=segment.annotations['rewardtime']
                data['rewards'][i,1]=segment.annotations['rewardframe']
            data['terrainlog']=[1];data['terrainlog'][0]=segment.annotations['terrain']
            data['terrainlog_secondstream']=[1];data['terrainlog_secondstream'][0]=segment.annotations['terrain_second']
            data['vin']=np.array(segment.analogsignals[4])
            data['vsig']=np.array(segment.analogsignals[6])
            data['vsyncintervals']=np.array(segment.analogsignals[7])
        else:
            #data['bgSweepFrames']=np.hstack((data['bgSweepFrames'],segment.analogsignals[8]))
            data['dx']=np.hstack((data['dx'],np.array(segment.analogsignals[2]*segment.analogsignals[1]).astype(float)))
            data['intervalsms']=np.hstack((data['intervalsms'],np.array(segment.analogsignals[5])))
            data['laps'][i,0]= segment.annotations['endtime']+data['starttime'];data['laps'][i,1]= segment.annotations['endframe']
            if lick:
                data['lickData']=np.hstack((data['lickData'],np.array(segment.spiketrains[0].times)))
            data['posx']=np.hstack((data['posx'],np.array(segment.analogsignals[0])))
            if segment.annotations['rewarded']:
                data['rewards'][i,0]=segment.annotations['rewardtime']
                data['rewards'][i,1]=segment.annotations['rewardframe']
            data['terrainlog'].append(segment.annotations['terrain'])
            data['terrainlog_secondstream'].append(segment.annotations['terrain_second'])
            data['vin']=np.hstack((data['vin'],np.array(segment.analogsignals[4])))
            data['vsig']=np.hstack((data['vsig'],np.array(segment.analogsignals[6])))
            data['vsyncintervals']=np.hstack((data['vsyncintervals'],np.array(segment.analogsignals[7])))
    
    #clean up rewards, removing unrewarded trials
    data['rewards']=data['rewards'][~np.all(data['rewards']==0,axis=1)]
    #reformat lick data into a tuple
    lick2 = np.zeros(np.shape(data['lickData'])[0]).astype(int)
    data['lickData']=(data['lickData'].astype(int),lick2)
    data['terrain']['log']=data['terrainlog']
    
    #return results
    pkl.dump(data,open(os.path.join(path,name),'wb'))
    print ''.join(('pkl saved to: ',os.path.join(path,name)))
    return data
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
#behavior utils----------------------------------------------------------------
#------------------------------------------------------------------------------
def convertStairsToDict(data):
    stairs  = data['staircase'].__dict__
    data['staircase'] = stairs
    return data


def createLapSegments_behavior(data,**kwargs):
#    create a neo segment for each lap, with appropriate metadata
#    optional inputs are:
#        clock
#            specify the clock all signals are referenced to
#            default is vstim, the refresh of the monitor
#        block
#            specify the neo block to which to add the segment list
#            if no block is input, then it creates a new one

    if 'clock' in kwargs.keys():
        clock = kwargs['clock']
        #sync specified clock to vstim
        if clock=='vstim':
            time =  computeUpdateTimes(data['vsyncintervals'],data['fps'])
        else:
            #output a time array that has the same number of frames as vsyncs, but in the specifiec timebase as opposed to vsync intervals
            time = np.array(1);
    else:
        clock = 'vstim'
        time =  computeUpdateTimes(data['vsyncintervals'],data['fps'])
        
    if 'block' in kwargs.keys():
        block = kwargs['block']
    else:
        block=neo.Block()
    
    if len(data['lickData']) > 1:
        lick=True
    else:
        lick=False   
        
    segmnts= []
    for i in range(len(data['terrainlog'])-1):#don't look at the last entry, as it was a lap started but not completed.
        s = neo.Segment(index=i,name=''.join(('lap ',str(i+1))),rec_datetime=data['startdatetime'])

        #compute some things for this lap
        lapstart, lapend = getLapIndex(data,encounterindex=i)
        x = np.array(data['posx'][lapstart:lapend])
        t = np.array(time[lapstart:lapend])/1000.0 #convert to seconds
        v = np.array(data['dx'][lapstart:lapend])/t
        a = v/t 
        
        #reward and stopping
        rewarded = getRewardInfo(data,t[0],t[len(t)-1])
        pauseTime = getPauseTime(x,t,data,i)
        isCorrect = getResponse(data,i,pauseTime)
        
        #licking
        if lick:
            licks= getLicksTrial(data['lickData'],lapstart, lapend)
        else:
            licks=np.nan
        
        #eye tracking
        if data['params']['eyetracker']:
            eyeX,eyeY = getEyeTraces(data['eyetrackerreport'])

        #optogenetics
        if data['optogenetics']:
            optoTrial = False#get whether or not this was an optoTrial
            optoTrace = np.zeros(10)#continuous representation of when the LED was on
            optoColor = 'blue'#where is this info in the data?

        #TODO: djd: add a quantities pixel unit here. need to know screen size and viewing distance
            #pix = pq.UnitQuantity('pixel',screenWidth*pq.meter/xPixels,symbol=''pix')
        
        #******************************************************************************
        #store metadata
        s.annotate(task=data['task']);
        s.annotate(terrain=data['terrainlog'][i])
        s.annotate(terrain_second=data['terrainlog_secondstream'][i])
        s.annotate(starttime=time[lapstart]/1000) #convert to seconds
        s.annotate(endtime=time[lapend]/1000) #convert to seconds
        s.annotate(startframe=lapstart)
        s.annotate(endframe=lapend)
        s.annotate(rewarded=rewarded[0])
        s.annotate(rewardtime=rewarded[1])
        s.annotate(rewardframe=rewarded[2])        
        s.annotate(selectiontime=getTerrainParameterLap(data,'selectiontime',i))
        s.annotate(pauseTime=pauseTime)
        s.annotate(correct=isCorrect)
        #other format of stim information
        #******************************************************************************
        
        #******************************************************************************
        #store analog signals
        s.analogsignals.append(neo.AnalogSignal(x,sampling_rate=data['fps']*pq.Hz,units=pq.meter,name='x'))
        s.analogsignals.append(neo.AnalogSignal(t,sampling_rate=data['fps']*pq.Hz,units=pq.second,name='t'))
        s.analogsignals.append(neo.AnalogSignal(v,sampling_rate=data['fps']*pq.Hz,units=pq.meter/pq.second,name='v'))
        s.analogsignals.append(neo.AnalogSignal(a,sampling_rate=data['fps']*pq.Hz,units=pq.meter/(pq.second*pq.second),name='a'))
        s.analogsignals.append(neo.AnalogSignal(np.array(data['vin'][lapstart:lapend]),sampling_rate=data['fps']*pq.Hz,units=pq.V,name='vin'))     
        s.analogsignals.append(neo.AnalogSignal(np.array(data['intervalsms'][lapstart:lapend]),sampling_rate=data['fps']*pq.Hz,units=pq.ms,name='intervalsms'))     
        s.analogsignals.append(neo.AnalogSignal(np.array(data['vsig'][lapstart:lapend]),sampling_rate=data['fps']*pq.Hz,units=pq.V,name='vsig'))     
        s.analogsignals.append(neo.AnalogSignal(np.array(data['vsyncintervals'][lapstart:lapend]),sampling_rate=data['fps']*pq.Hz,units=pq.ms,name='vsyncintervals'))     
       # s.analogsignals.append(neo.AnalogSignal(np.array(data['bgSweepFrames'][lapstart:lapend]),sampling_rate=data['fps']*pq.Hz,units=pq.ms,name='bgSweepFrames'))     
        if data['params']['eyetracker']:
            s.analogsignals.append(neo.AnalogSignal(eyeX,sampling_rate=data['fps']*pq.Hz,units=pq.meter))
            s.analogsignals.append(neo.AnalogSignal(eyeY,sampling_rate=data['fps']*pq.Hz,units=pq.meter))
        #******************************************************************************
        
        #******************************************************************************
        #store spike trains
        if lick:
            s.spiketrains.append(neo.SpikeTrain(licks,units='sec',t_stop=lapend,name='licks'))        
  #      s.spiketrains.append(neo.SpikeTrain())#rewards
        #******************************************************************************
        
        block.segments.append(s)
    #segmnts.annotate(data=data)
    return block

    
def computeUpdateTimes(vsyncintervals,fps):
    vsyncintervals = getvsyncintervals(vsyncintervals,fps)
    t = [0]
    for i,v in enumerate(vsyncintervals):
        t.append((t[i]+v))        
    t.append(np.nan)#add one to balance
    return np.array(t)
        
def getvsyncintervals(vsyncintervals,fps):
    if fps == 180:
        for i in range(np.shape(vsyncintervals)[0]):
            if i%3==0:
                vsyncintervals[i:i+2]=vsyncintervals[i]/3
    else:
        vsyncintervals=vsyncintervals
    return vsyncintervals
            
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
            return (rewarded,data['rewards'][i,0],data['rewards'][i,1])
    return (rewarded,np.nan,np.nan)

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
    if startIndex>=0 and endIndex>=0:
        return lickData[0][startIndex:endIndex]
    else:
        return np.nan
            
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------




        
    
    








#TODO djd: I/O for other file formats
         
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
