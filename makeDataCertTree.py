import ROOT
import sys,os
import numpy
import array
import math
import argparse
import pickle
import time

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--pccfile', type=str, default="", help='The pccfile to input (pixel clusters and vertices)')
parser.add_argument('--brildir', type=str, default="brildata", help='bril data is here')
parser.add_argument('--nobril', default=False, action="store_true", help="Don\'t process bril data (default false)")
parser.add_argument('--beamonly', default=False, action="store_true", help="BRIL data only contains beam info")
parser.add_argument('-l','--label',type=str,default="",  help="Label for output file")
parser.add_argument('--minfill', type=int, default=3818, help="Minimum fill number")
parser.add_argument('--minrun',  type=int, default=230000,help="Minimum run number")
parser.add_argument('--isBatch', default=False, action="store_true", help="Doesn't pop up plots and only fills tree when CMS and BRIL data are present")
parser.add_argument('-v', '--includeVertices', default=True, action="store_false", help="Include vertex counting (default true)")
parser.add_argument('--eventBased', default=False, action="store_true", help="PCC ntuples are event based (default false--typically LS-based)")
parser.add_argument('--outPath', default="", help="The path for the output file")
#parser.add_argument('--perBX', type=bool, default=False, action="store_true", help="Store PC lumi per BX")
#                if args.perBX:

args = parser.parse_args()

if args.nobril:
    args.brildir=""


vetoList=[302126344,  302123024,  302122768,  302057496,  302123804,  302124308,  
302126364,  302188820]
f_LHC = 11245.6
t_LS=math.pow(2,18)/f_LHC
xsec_ub=80000. #microbarn


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


weightThreshold=1e-5

# the value is already summed over weight
def AverageWithWeight(list):
    sumValue=0
    sumWeight=0
    for value,weight in list:
        sumValue=sumValue+value
        sumWeight=sumWeight+weight

    if sumWeight>0:
        return float(sumValue)/sumWeight

def GetWeightedValues(list):
    count=0
    sumOfWeights=0
    sumOfWeights2=0
    weightedSum=0

    for value,weight in list:
        #print value,weight
        if weight<weightThreshold:
            continue
        count=count+1
        sumOfWeights=sumOfWeights+weight
        sumOfWeights2=sumOfWeights2+math.pow(weight,2)
        weightedSum=weightedSum+weight*value

    return count,sumOfWeights,sumOfWeights2,weightedSum


def GetMean(list):
    #print "list length",len(list)
    count,sumOfWeights,sumOfWeights2,weightedSum=GetWeightedValues(list)
    mean=GetMeanFromWeightedValues(sumOfWeights,weightedSum)
    return mean


def GetMeanFromWeightedValues(sumOfWeights,weightedSum):
    mean=0
    if sumOfWeights>0:
        mean=weightedSum/sumOfWeights
    return mean


def GetMeanAndMeanError(list):
    count,sumOfWeights,sumOfWeights2,weightedSum=GetWeightedValues(list)
    if sumOfWeights2==0:
        return -99,-99
    neff=math.pow(sumOfWeights,2)/sumOfWeights
    mean=GetMeanFromWeightedValues(sumOfWeights,weightedSum)

    #print neff,count,sumOfWeights
    
    weightedSumDiffFromAve2=0
    for value,weight in list:
        if weight<weightThreshold:
            continue
        weightedSumDiffFromAve2=weightedSumDiffFromAve2+weight*math.pow(value-mean,2) 

    stddev=0
    meanError=0
    if count>2:
        stddev=math.sqrt( weightedSumDiffFromAve2 / (sumOfWeights))
        meanError=stddev/math.sqrt(neff)

    #print "stddev",stddev

    return mean,meanError



startTime=time.time()
onlineLumi={} #(fill,run,LS)
runInfo={}

if not args.nobril:
    files=os.listdir(args.brildir)
    files.sort()
    for fileName in files:
        print fileName,"this dict size",
        if fileName.find(".pkl") !=-1:
            try:
                filePath=args.brildir+"/"+fileName
                pklFile=open(filePath,'rb')
                data=pickle.load(pklFile)
                print len(data),
                if data.has_key("runInfo"):
                    for runInfoKey in data["runInfo"]:
                        if not runInfo.has_key(runInfoKey):
                            runInfo[runInfoKey]={}
                        runInfo[runInfoKey].update(data["runInfo"][runInfoKey])
                onlineLumi.update(data)
                pklFile.close()
            except:
                print "Problem with pickle file",
        else:
            continue

        print " new total LSs: ",len(onlineLumi)

print runInfo

endTime=time.time()
print "Duration: ",endTime-startTime

maxLS={}
    
goodVertexCounts={}
validVertexCounts={}
PCCsPerLS={}
lumiEstimate={}
# key is bx,LS and LS

if args.outPath!="":
    outpath=args.outPath
    
    if outpath.find("/store")==0:
        outpath="root://eoscms//eos/cms"+outpath

if args.pccfile!="":
    filename=args.pccfile

    if filename.find("/store")==0: # file is in eos
        filename="root://eoscms//eos/cms"+filename
    
    tfile=ROOT.TFile.Open(filename)
    
    tree=tfile.Get("lumi/tree")
    
    tree.SetBranchStatus("*",0)
    if args.includeVertices:
        tree.SetBranchStatus("nGoodVtx*",1)
        tree.SetBranchStatus("nValidVtx*",1)
    tree.SetBranchStatus("run*",1)
    tree.SetBranchStatus("LS*",1)
    tree.SetBranchStatus("event*",1)
    tree.SetBranchStatus("nPixelClusters*",1)
    tree.SetBranchStatus("layer*",1)
    tree.SetBranchStatus("BXNo",1)

    nentries=tree.GetEntries()
  
    for iev in range(nentries):
        tree.GetEntry(iev)
        if iev%1000==0:
            print "iev,",iev
            print "(tree.run,tree.LS)",tree.run,tree.LS
            print "len(tree.nPixelClusters)",len(tree.nPixelClusters)
            print "len(tree.layers)",len(tree.layers)
        if len(tree.nPixelClusters)==0:
            continue
        
        LSKey=(tree.run,tree.LS)
        
        if args.includeVertices:
            if LSKey not in goodVertexCounts:
                goodVertexCounts[LSKey]=[]
                goodVertexCounts[LSKey].append([])
                goodVertexCounts[LSKey].append({})
                validVertexCounts[LSKey]=[]
                validVertexCounts[LSKey].append([])
                validVertexCounts[LSKey].append({})
                for bx,counts in tree.BXNo:
                    goodVertexCounts[LSKey][1][bx]=[]
                    validVertexCounts[LSKey][1][bx]=[]
    
            for ibx,nGoodVtx in tree.nGoodVtx:
                goodVertexCounts[LSKey][0].append([nGoodVtx,tree.BXNo[ibx]])
                goodVertexCounts[LSKey][1][ibx].append([nGoodVtx,tree.BXNo[ibx]])
            for ibx,nValidVtx in tree.nValidVtx:
                validVertexCounts[LSKey][0].append([nValidVtx,tree.BXNo[ibx]])
                validVertexCounts[LSKey][1][ibx].append([nValidVtx,tree.BXNo[ibx]])
       
        #for ibx in tree.BXNo:
        #    print "BXNo", ibx[0], ibx[1]
       
        # 0 is the total count for layers 2-5
        # 1-5 is the count for layre 1-5
        # 6 is the count for per BX

        PCCsPerEntry={}
        bxids=[]
        if PCCsPerEntry.has_key((tree.run,tree.LS)) == 0:
            PCCsPerEntry[(tree.run,tree.LS)]=[0]*6
            PCCsPerEntry[(tree.run,tree.LS)].append({}) # for bx->counts
       
        if PCCsPerLS.has_key((tree.run,tree.LS)) == 0:
            PCCsPerLS[(tree.run,tree.LS)]=[[] for x in xrange(6)]
            PCCsPerLS[(tree.run,tree.LS)].append({})
    
        if not maxLS.has_key(tree.run):
            maxLS[tree.run]=0
        
        if tree.LS>maxLS[tree.run]:
            maxLS[tree.run]=tree.LS+5
    
        layerNumbers=[]
        for item in tree.layers:
            layerNumbers.append(item[1])
    
        counter=0
        bxid=-1
        for item in tree.nPixelClusters:
            bxid=item[0][0]
            module=item[0][1]
            layer=tree.layers[module]
            clusters=item[1]
   
            if module in vetoList:
                continue

            if layer==6:
                layer=1
    
            PCCsPerEntry[(tree.run,tree.LS)][layer]=PCCsPerEntry[(tree.run,tree.LS)][layer]+clusters
            if not PCCsPerEntry[(tree.run,tree.LS)][6].has_key(bxid):
                PCCsPerEntry[(tree.run,tree.LS)][6][bxid]=0
    
            if layer!=1:
                PCCsPerEntry[(tree.run,tree.LS)][6][bxid]=PCCsPerEntry[(tree.run,tree.LS)][6][bxid]+clusters
                PCCsPerEntry[(tree.run,tree.LS)][0]=PCCsPerEntry[(tree.run,tree.LS)][0]+clusters
    
            if bxid not in bxids:
               bxids.append(bxid)
        counter=counter+1
  
        if not args.eventBased: #divide by the sum of events
            PCCsPerEntry[(tree.run,tree.LS)][0]=PCCsPerEntry[(tree.run,tree.LS)][0]/float(tree.eventCounter)
            for layer in range(1,6):
                PCCsPerEntry[(tree.run,tree.LS)][layer]=PCCsPerEntry[(tree.run,tree.LS)][layer]/float(tree.eventCounter)
            for bxid in bxids:
                PCCsPerEntry[(tree.run,tree.LS)][6][bxid]=PCCsPerEntry[(tree.run,tree.LS)][6][bxid]/float(tree.BXNo[bxid])

        PCCsPerLS[(tree.run,tree.LS)][0].append([PCCsPerEntry[(tree.run,tree.LS)][0],1])
        for layer in range(1,6):
            PCCsPerLS[(tree.run,tree.LS)][layer].append([PCCsPerEntry[(tree.run,tree.LS)][layer],1])
        for bxid in bxids:
            if not PCCsPerLS[(tree.run,tree.LS)][6].has_key(bxid):
                PCCsPerLS[(tree.run,tree.LS)][6][bxid]=[]
            PCCsPerLS[(tree.run,tree.LS)][6][bxid].append([PCCsPerEntry[(tree.run,tree.LS)][6][bxid],1])


cmskeys=PCCsPerLS.keys()
brilkeys=onlineLumi.keys()
if "runInfo" in brilkeys:
    brilkeys.remove("runInfo")


LSKeys=list(set(cmskeys+brilkeys))
# if batch only look at keys in both
if args.isBatch:
    if args.nobril or args.beamonly:
        LSKeys=cmskeys
    else:
        LSKeys=list(set(cmskeys).intersection(brilkeys))
    
LSKeys.sort()

newfilename="dataCertification_"+str(LSKeys[0][0])+"_"+str(LSKeys[-1][0])+"_"+args.label+".root"
if args.outPath!="":
    newfilename=outpath+"/"+newfilename
newfile=ROOT.TFile.Open(newfilename,"RECREATE")
newtree=ROOT.TTree("certtree","validationtree")

fill= array.array( 'I', [ 0 ] )
run = array.array( 'I', [ 0 ] )
LS  = array.array( 'I', [ 0 ] )
nBX = array.array( 'I', [ 0 ] )
nActiveBX = array.array( 'I', [ 0 ] )
nBXHF = array.array( 'I', [ 0 ] )
nBXBCMF = array.array( 'I', [ 0 ] )
nBXPLT = array.array( 'I', [ 0 ] )

nCluster    = array.array( 'd', [ 0 ] )
nClusterError    = array.array( 'd', [ 0 ] )
nPCPerLayer = array.array( 'd', 5*[ 0 ] )

HFLumi    = array.array( 'd', [ 0 ] )
BCMFLumi  = array.array( 'd', [ 0 ] )
PLTLumi   = array.array( 'd', [ 0 ] )
BestLumi  = array.array( 'd', [ 0 ] )
BestLumi_PU  = array.array( 'd', [ 0 ] )
PC_PU  = array.array( 'd', [ 0 ] )

HFLumi_perBX = array.array( 'd', 3600*[ -1 ] )
BCMFLumi_perBX = array.array( 'd', 3600*[ -1 ] )
PLTLumi_perBX = array.array('d', 3600*[ -1 ] )

HFBXid = array.array('I', 3600*[ 0 ] )
BCMFBXid = array.array('I', 3600*[ 0 ] )
PLTBXid = array.array('I', 3600*[ 0 ] )

HFLumi_integrated    = array.array( 'd', [ 0 ] )
BCMFLumi_integrated  = array.array( 'd', [ 0 ] )
PLTLumi_integrated   = array.array( 'd', [ 0 ] )
BestLumi_integrated  = array.array( 'd', [ 0 ] )

hasBrilData = array.array('b', [0])
hasCMSData  = array.array('b', [0])

PC_lumi_B0      = array.array( 'd', [ 0 ] )
PC_lumi_B3p8    = array.array( 'd', [ 0 ] )
PC_lumi_integrated_B0      = array.array( 'd', [ 0 ] )
PC_lumi_integrated_B3p8    = array.array( 'd', [ 0 ] )
PC_lumi_integrated_error_B0      = array.array( 'd', [ 0 ] )
PC_lumi_integrated_error_B3p8    = array.array( 'd', [ 0 ] )

PC_lumi_B0_perBX  = array.array('d', 3600*[ 0 ])
PC_lumi_B3p8_perBX = array.array('d', 3600*[ 0 ])

PC_xsec         = array.array( 'd', [ 0 ] )
PC_xsec_layers  = array.array( 'd', 5*[ 0 ] )

nPCPerBXid  = array.array( 'd', 3600*[ 0 ] )
PCBXid        = array.array( 'I', 3600*[ 0 ] )

goodVertices  = array.array( 'd', [ 0 ] )
goodVertices_xsec  = array.array( 'd', [ 0 ] )
goodVertices_eff  = array.array( 'd', [ 0 ] )

goodVertices_perBX  = array.array( 'd', 3600*[ 0 ] )
goodVertices_perBX_xsec  = array.array( 'd', 3600*[ 0 ] )
goodVertices_perBX_eff  = array.array( 'd', 3600*[ 0 ] )

validVertices  = array.array( 'd', [ 0 ] )
validVertices_xsec  = array.array( 'd', [ 0 ] )
validVertices_eff  = array.array( 'd', [ 0 ] )

validVertices_perBX  = array.array( 'd', 3600*[ 0 ] )
validVertices_perBX_xsec  = array.array( 'd', 3600*[ 0 ] )
validVertices_perBX_eff  = array.array( 'd', 3600*[ 0 ] )



newtree.Branch("fill",fill,"fill/I")
newtree.Branch("run",run,"run/I")
newtree.Branch("LS",LS,"LS/I")
newtree.Branch("nActiveBX",nActiveBX,"nActiveBX/I")
newtree.Branch("nBX",nBX,"nBX/I")
newtree.Branch("nBXHF", nBXHF, "nBXHF/I")
newtree.Branch("nBXBCMF", nBXBCMF, "nBXBCMF/I")
newtree.Branch("nBXPLT", nBXPLT, "nBXPLT/I")

newtree.Branch("nCluster",nCluster,"nCluster/D")
newtree.Branch("nClusterError",nClusterError,"nClusterError/D")
newtree.Branch("nPCPerLayer",nPCPerLayer,"nPCPerLayer[5]/D")

newtree.Branch("PC_lumi_B0",PC_lumi_B0,"PC_lumi_B0/D")
newtree.Branch("PC_lumi_B3p8",PC_lumi_B3p8,"PC_lumi_B3p8/D")
newtree.Branch("PC_lumi_integrated_B0",PC_lumi_integrated_B0,"PC_lumi_integrated_B0/D")
newtree.Branch("PC_lumi_integrated_B3p8",PC_lumi_integrated_B3p8,"PC_lumi_integrated_B3p8/D")
newtree.Branch("PC_lumi_integrated_error_B0",PC_lumi_integrated_error_B0,"PC_lumi_integrated_error_B0/D")
newtree.Branch("PC_lumi_integrated_error_B3p8",PC_lumi_integrated_error_B3p8,"PC_lumi_integrated_error_B3p8/D")

newtree.Branch("PC_lumi_B0_perBX", PC_lumi_B0_perBX, "PC_lumi_B0_perBX[nBX]/D")
newtree.Branch("PC_lumi_B3p8_perBX", PC_lumi_B3p8_perBX, "PC_lumi_B3p8_perBX[nBX]/D")

newtree.Branch("PC_xsec",PC_xsec,"PC_xsec/D")
newtree.Branch("PC_xsec_layers",PC_xsec_layers,"PC_xsec_layers[5]/D")

newtree.Branch("PCBXid",PCBXid,"PCBXid[nBX]/I")
newtree.Branch("nPCPerBXid",nPCPerBXid,"nPCPerBXid[nBX]/D")

newtree.Branch("BestLumi",BestLumi,"BestLumi/D")
newtree.Branch("HFLumi",HFLumi,"HFLumi/D")
newtree.Branch("BCMFLumi",BCMFLumi,"BCMFLumi/D")
newtree.Branch("PLTLumi",PLTLumi,"PLTLumi/D")

newtree.Branch("HFLumi_perBX", HFLumi_perBX, "HFLumi_perBX[nBXHF]/D")
newtree.Branch("BCMFLumi_perBX", BCMFLumi_perBX, "BCMFLumi_perBX[nBXBCMF]/D")
newtree.Branch("PLTLumi_perBX", PLTLumi_perBX, "PLTLumi_perBX[nBXPLT]/D")

newtree.Branch("HFBXid", HFBXid, "HFBXid[nBXHF]/I")
newtree.Branch("BCMFBXid", BCMFBXid, "BCMFBXid[nBXBCMF]/I")
newtree.Branch("PLTBXid", PLTBXid, "PLTBXid[nBXPLT]/I")

newtree.Branch("BestLumi_integrated",BestLumi_integrated,"BestLumi_integrated/D")
newtree.Branch("HFLumi_integrated",HFLumi_integrated,"HFLumi_integrated/D")
newtree.Branch("BCMFLumi_integrated",BCMFLumi_integrated,"BCMFLumi_integrated/D")
newtree.Branch("PLTLumi_integrated",PLTLumi_integrated,"PLTLumi_integrated/D")

newtree.Branch("BestLumi_PU",BestLumi_PU,"BestLumi_PU/D")
newtree.Branch("PC_PU",PC_PU,"PC_PU/D")

newtree.Branch("hasBrilData",hasBrilData,"hasBrilData/O")
newtree.Branch("hasCMSData",hasCMSData,"hasCMSData/O")

newtree.Branch("goodVertices",      goodVertices,     "goodVertices/D")
newtree.Branch("goodVertices_xsec", goodVertices_xsec,"goodVertices_xsec/D")
newtree.Branch("goodVertices_eff",  goodVertices_eff, "goodVertices_eff/D")
newtree.Branch("goodVertices_perBX",      goodVertices_perBX,     "goodVertices_perBX[nBX]/D")
newtree.Branch("goodVertices_perBX_xsec", goodVertices_perBX_xsec,"goodVertices_perBX_xsec[nBX]/D")
newtree.Branch("goodVertices_perBX_eff",  goodVertices_perBX_eff, "goodVertices_perBX_eff[nBX]/D")

newtree.Branch("validVertices",      validVertices,     "validVertices/D")
newtree.Branch("validVertices_xsec", validVertices_xsec,"validVertices_xsec/D")
newtree.Branch("validVertices_eff",  validVertices_eff, "validVertices_eff/D")
newtree.Branch("validVertices_perBX",      validVertices_perBX,     "validVertices_perBX[nBX]/D")
newtree.Branch("validVertices_perBX_xsec", validVertices_perBX_xsec,"validVertices_perBX_xsec[nBX]/D")
newtree.Branch("validVertices_perBX_eff",  validVertices_perBX_eff, "validVertices_perBX_eff[nBX]/D")


PC_calib_xsec={}
PC_calib_xsec["B0_pp13TeV"]=9.4e6
PC_calib_xsec["B3p8_pp13TeV"]=9.4e6
# scale with PLT 3.51E-28/4.95E-28*9.4
PC_calib_xsec["B0_pp5TeV"]=6.7e6
PC_calib_xsec["B3p8_pp5TeV"]=6.7e6

collisionType="pp5TeV"

hists={}
PCCPerLayer=[118.,44.3,39.2,34.9,22.3,23.9] #from MC
for key in LSKeys:
    run[0]=key[0]
    LS[0]=key[1]

    takenHF=False
    if runInfo.has_key("nActiveBXHF"):
        try:
            if runInfo["nActiveBXHF"].has_key(run[0]):
                if int(runInfo["nActiveBXHF"][run[0]])>0:
                    nActiveBX[0]=int(runInfo["nActiveBXHF"][run[0]])
                    takenHF=True
        except:
            takenHF=False
    if runInfo.has_key("nActiveBXBEAMINFO") and not takenHF:
        if runInfo["nActiveBXBEAMINFO"].has_key(run[0]):
            nActiveBX[0]=int(runInfo["nActiveBXBEAMINFO"][run[0]])
        else:
            print "no",run[0],"among keys"
        

    hasBrilData[0]=False
    hasCMSData[0]=False
    
    HFLumi[0]=-1
    BestLumi[0]=-1
    PLTLumi[0] =-1
    BCMFLumi[0]=-1
    
    HFLumi_integrated[0]=-1
    BestLumi_integrated[0]=-1
    PLTLumi_integrated[0] =-1
    BCMFLumi_integrated[0]=-1
        
    BestLumi_PU[0]=-1
    PC_PU[0]=-1
    PC_xsec[0]=-1

    PC_lumi_B0[0]=-1
    PC_lumi_B3p8[0]=-1
    PC_lumi_integrated_B0[0]=-1
    PC_lumi_integrated_B3p8[0]=-1
    PC_lumi_integrated_error_B0[0]=-1
    PC_lumi_integrated_error_B3p8[0]=-1

    goodVertices[0]=-1
    goodVertices_xsec[0]=-1
    goodVertices_eff[0]=-1

    validVertices[0]=-1
    validVertices_xsec[0]=-1
    validVertices_eff[0]=-1

    for layer in range(0,5):
        PC_xsec_layers[layer]=-1
        nPCPerLayer[layer]=-1

    if key in brilkeys:
        try:
            hasBrilData[0]=True
            fill[0]=int(onlineLumi[key]['fill'])
            if onlineLumi[key].has_key('best'):
                BestLumi_integrated[0]=float(onlineLumi[key][onlineLumi[key]['best']])
                BestLumi[0]=BestLumi_integrated[0]
            else:
                BestLumi_integrated[0]=float(onlineLumi[key]['PLTZERO'])
                BestLumi[0]=BestLumi_integrated[0]
            if onlineLumi[key].has_key('PU_best'):
                BestLumi_PU[0]=float(onlineLumi[key]['PU_best'])
                
            if BestLumi[0]>0:
                BestLumi[0]=BestLumi[0]/t_LS
            if onlineLumi[key].has_key('HFOC'):
                HFLumi_integrated[0]=float(onlineLumi[key]['HFOC'])
                HFLumi[0]=HFLumi_integrated[0]
                if HFLumi[0]>0:
                    HFLumi[0]=HFLumi[0]/t_LS
            if onlineLumi[key].has_key('PLTZERO'):
                PLTLumi_integrated[0]=float(onlineLumi[key]['PLTZERO'])
                PLTLumi[0]=PLTLumi_integrated[0]
                if PLTLumi[0]>0:
                    PLTLumi[0]=PLTLumi[0]/t_LS
            if onlineLumi[key].has_key('BCM1F'):
                BCMFLumi_integrated[0]=float(onlineLumi[key]['BCM1F'])
                BCMFLumi[0]=BCMFLumi_integrated[0]
                if BCMFLumi[0]>0:
                    BCMFLumi[0]=BCMFLumi[0]/t_LS

            if onlineLumi[key].has_key('HFOC_BX'):
                nBXHF[0] = len(onlineLumi[key]['HFOC_BX'])
                idxHF=0
                HFbxkeys = onlineLumi[key]['HFOC_BX'].keys()
                HFbxkeys.sort()
                #print "HF length", len(HFbxkeys)
                for HFbxkey in HFbxkeys :
                    HFBXid[idxHF] = int(HFbxkey)
                    HFLumi_perBX[idxHF] = float(onlineLumi[key]['HFOC_BX'][HFbxkey])/t_LS
                    idxHF = idxHF+1
            

            if onlineLumi[key].has_key('PLTZERO_BX'):
                nBXPLT[0] = len(onlineLumi[key]['PLTZERO_BX'])
                idxPLT=0
                PLTbxkeys = onlineLumi[key]['PLTZERO_BX'].keys()
                PLTbxkeys.sort()
                #print PLTbxkeys
                for PLTbxkey in PLTbxkeys :
                    PLTBXid[idxPLT] = int(PLTbxkey)
                    PLTLumi_perBX[idxPLT] = float(onlineLumi[key]['PLTZERO_BX'][PLTbxkey])/t_LS
                    idxPLT = idxPLT+1
        
            if onlineLumi[key].has_key('BCM1F_BX'):
                nBXBCMF[0] = len(onlineLumi[key]['BCM1F_BX'])
                idxBCMF=0
                BCMFbxkeys = onlineLumi[key]['BCM1F_BX'].keys()
                BCMFbxkeys.sort()
                #print len(BCMFbxkeys)
                for BCMFbxkey in BCMFbxkeys :
                    BCMFBXid[idxBCMF] = int(BCMFbxkey)
                    BCMFLumi_perBX[idxBCMF] = float(onlineLumi[key]['BCM1F_BX'][BCMFbxkey])/t_LS
                    idxBCMF = idxBCMF+1
               
                
        except:
            print "Failed in brilkey",key#,onlineLumi[key]

    if key in cmskeys:
        try:
            hasCMSData[0]=True
            nBX[0]=len(tree.BXNo)
            count=0
            if args.includeVertices:
                goodVertices[0]=AverageWithWeight(goodVertexCounts[key][0])
                validVertices[0]=AverageWithWeight(validVertexCounts[key][0])
                bxids=goodVertexCounts[key][1].keys()
                bxids.sort()
                
                ibx=0
                for bxid in bxids:
                    goodVertices_perBX[ibx]=AverageWithWeight(goodVertexCounts[key][1][bxid])
                    validVertices_perBX[ibx]=AverageWithWeight(validVertexCounts[key][1][bxid])
                    ibx=ibx+1

            for PCCs in PCCsPerLS[key]:
                #print key,count
                if count==0:
                    mean,error=GetMeanAndMeanError(PCCs)
                    nCluster[0]=mean
                    nClusterError[0]=error
                elif count<6:
                    mean,error=GetMeanAndMeanError(PCCs)
                    nPCPerLayer[count-1]=mean
                else:
                    ibx=0
                    bxids=PCCs.keys()
                    bxids.sort()
                    for bxid in bxids:
                        if bxid<0: 
                            continue
                        mean,error=GetMeanAndMeanError(PCCs[bxid])
                        PCBXid[ibx]=bxid
                        nPCPerBXid[ibx]=mean
                        totalPCperBX=mean*math.pow(2,18)
                        PC_lumi_B0_perBX[ibx]=totalPCperBX/PC_calib_xsec["B0_"+collisionType]/t_LS
                        PC_lumi_B3p8_perBX[ibx]=totalPCperBX/PC_calib_xsec["B3p8_"+collisionType]/t_LS

                        ibx=ibx+1
                        if ibx>nBX[0]:
                            print "ibx,nBX[0],",ibx,nBX[0],", but WHY?!!!"

                count=count+1 
            totalPC=nCluster[0]*math.pow(2,18)*nActiveBX[0]
            totalPCError=nClusterError[0]*math.pow(2,18)*nActiveBX[0]
            
            PC_lumi_B0[0]=totalPC/PC_calib_xsec["B0_"+collisionType]/t_LS
            PC_lumi_B3p8[0]=totalPC/PC_calib_xsec["B3p8_"+collisionType]/t_LS
            PC_lumi_integrated_B0[0]=totalPC/PC_calib_xsec["B0_"+collisionType]
            PC_lumi_integrated_B3p8[0]=totalPC/PC_calib_xsec["B3p8_"+collisionType]
            PC_lumi_integrated_error_B0[0]=totalPCError/PC_calib_xsec["B0_"+collisionType]
            PC_lumi_integrated_error_B3p8[0]=totalPCError/PC_calib_xsec["B3p8_"+collisionType]
            
        except:
            print "Failed in cmskey",key
            
    if hasCMSData[0] and hasBrilData[0]: 
        try:
            totalOrbitsPerLS=math.pow(2,18)*nActiveBX[0]
            PC_xsec[0]=nCluster[0]/BestLumi_integrated[0]*totalOrbitsPerLS
            if args.includeVertices:
                goodVertices_xsec[0]=goodVertices[0]/BestLumi_integrated[0]*totalOrbitsPerLS
                goodVertices_eff[0]=goodVertices_xsec[0]/xsec_ub
                validVertices_xsec[0]=validVertices[0]/BestLumi_integrated[0]*totalOrbitsPerLS
                validVertices_eff[0]=validVertices_xsec[0]/xsec_ub
                ibx=0
                for bxid in bxids:
                    # FIXME I should really use the lumi for this bx and not multiply by number of bxs
                    goodVertices_perBX_xsec[ibx]=goodVertices_perBX[ibx]/BestLumi_integrated[0]*math.pow(2,18)*nActiveBX[0]
                    goodVertices_perBX_eff[ibx]=goodVertices_perBX_xsec[ibx]/xsec_ub
                    validVertices_perBX_xsec[ibx]=validVertices_perBX[ibx]/BestLumi_integrated[0]*math.pow(2,18)*nActiveBX[0]
                    validVertices_perBX_eff[ibx]=validVertices_perBX_xsec[ibx]/xsec_ub
                    ibx=ibx+1
            
            for layer in range(0,5):
                PC_xsec_layers[layer]=nPCPerLayer[layer]/BestLumi_integrated[0]*totalOrbitsPerLS
            if BestLumi_PU[0]==0 and BestLumi[0]>0 and nActiveBX[0]>0:
                BestLumi_PU[0]=BestLumi[0]*xsec_ub/nActiveBX[0]/f_LHC
            
            if PC_lumi_B3p8[0]>0 and nActiveBX[0]>0:
                PC_PU[0]=PC_lumi_B3p8[0]*xsec_ub/nActiveBX[0]/f_LHC
                
        except:
            print "Failed cms+bril computation",key,onlineLumi[key]

    newtree.Fill()

newfile.Write()
newfile.Close()

