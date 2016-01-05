import ROOT
import sys
import os
import json
import argparse

parser = argparse.ArgumentParser(description='Produce a JSON file of the run,LS from ROOT tree.')
parser.add_argument('-r', '--rootfilename', type=str, default="", help='The data certification file.')
parser.add_argument('-j', '--jsonfilename', type=str, default="", help='JSON file of run/LSs to filter.')
parser.add_argument('-l', '--label',    type=str, default="", help="Label for output file")
parser.add_argument('-t', '--treename', type=str, default="certtree", help="Tree name (default:  certtree)")
args = parser.parse_args()

if args.rootfilename=="" or args.jsonfilename=="":
    print "Re-run giving '-r ROOTFILENAME' and '-j JSONFILENAME' as agruments"
    sys.exit(1)




tfile=ROOT.TFile(args.rootfilename)
runLSData = json.load(open(args.jsonfilename))


def IsRunLSInList(run,LS):
    if not runLSData.has_key(str(run)):
        return False

    else:
        for LSRange in runLSData[str(run)]:
            if int(LSRange[0])<=LS and int(LSRange[1])>=LS:
                return True

        return False
                

tree1=tfile.Get(args.treename)

newrootfilename=args.rootfilename.split(".")[0]+"_filtered.root"
newtfile=ROOT.TFile(newrootfilename,"RECREATE")
tree2=tree1.CloneTree(0)

nentries=tree1.GetEntries()

for ient in range(nentries):
    tree1.GetEntry(ient)
    
    if not IsRunLSInList(tree1.run,tree1.LS):
        tree2.Fill()

print tree1.GetEntries(),tree2.GetEntries()

newtfile.Write()
