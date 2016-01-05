import ROOT
import sys,os
import math
import argparse

parser = argparse.ArgumentParser(description='Produce a JSON file of the run,LS from ROOT tree.')
parser.add_argument('-f', '--filename', type=str, default="", help='The ROOT file.')
parser.add_argument('-d', '--dir',      type=str, default="", help='The ROOT files\' directory.')
parser.add_argument('-l', '--label',    type=str, default="", help="Label for output file")
parser.add_argument('-t', '--treename', type=str, default="certtree", help="Tree name")
parser.add_argument('-r', '--runsonly', default=False, action='store_true', help="Make dummy json file containing runs")
args = parser.parse_args()

if args.filename=="" and args.dir=="":
    print "Re-run giving '-f FILENAME' or '-d PATH' as agrument"
    sys.exit(1)


def MakeListOfLists(inputList):
    outputList = []
    inputList.sort()
    firstLS = -1
    lastLS = -1
    for lumiSect in inputList:
        if firstLS == -1:
            firstLS = lumiSect
        if lastLS == -1:
            lastLS = lumiSect
        if lumiSect - lastLS == 1:
            lastLS = lumiSect 
        elif lumiSect - lastLS > 1:
            myList = [firstLS, lastLS]
            outputList.append(myList)
            firstLS = lumiSect
            lastLS = lumiSect
        if lumiSect == inputList[-1]:    
            myList = [firstLS, lastLS]
            outputList.append(myList)
    return outputList

# order the contents of inputList
# loop through contents of inputList
# variable outside loop containing what the first entry of the list should be
# append loop list to outputList

filenames=[]
if args.filename!="":
    filenames.append(args.filename)

if args.dir!="":
    dirfilenames=os.listdir(args.dir)
    for dirfilename in dirfilenames:
        filenames.append(args.dir+"/"+dirfilename)

LSbyRun={}

for filename in filenames:
    print filename
    if filename.find(".root")==-1:
        continue
    tfile=ROOT.TFile(filename)
    tree=tfile.Get(args.treename)
    
    tree.SetBranchStatus("*",0)
    tree.SetBranchStatus("run",1)
    tree.SetBranchStatus("LS",1)
    
    nentries=tree.GetEntries()

    for ient in range(nentries):
        tree.GetEntry(ient)
        if not LSbyRun.has_key(tree.run):
            LSbyRun[tree.run]=[]
        if tree.LS not in LSbyRun[tree.run]:
            LSbyRun[tree.run].append(tree.LS)


sortedRuns=LSbyRun.keys()
sortedRuns.sort()
outFileName="jsonOfReadRunLSs"+args.label+"_"+str(sortedRuns[0])+"_"+str(sortedRuns[-1])
if args.runsonly:
    outFileName=outFileName+"_runsOnly"
outFileName=outFileName+".txt"

textFile = open(outFileName,"w")

textFile.write('{')
for run in sortedRuns:
    if not args.runsonly:
        newList = MakeListOfLists(LSbyRun[run])
        newListStr=str(newList)
    else:
        newListStr='[[0,999999]]'
    
    strToWrite="\"" + str(run) + "\": " + newListStr
    if run != sortedRuns[-1]:
        strToWrite=strToWrite+','
        
    strToWrite=strToWrite+'\n'

    textFile.write(strToWrite)

textFile.write('}')
textFile.close()
