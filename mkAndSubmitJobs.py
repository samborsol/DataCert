import ROOT
import sys
import argparse
import os
import subprocess

parser=argparse.ArgumentParser()
parser.add_argument("-p",  "--path",  help="EOS path to PCCNTuples... /store/user/..")
parser.add_argument("-d",  "--dir", default="JobsDir", help="Output directory")
parser.add_argument('--minfill', type=int, default=3818, help="Minimum fill number")
parser.add_argument("-s",  "--sub", action='store_true', default=False, help="bsub created jobs")
parser.add_argument("--brildir", type=str, default="../brildata", help="Path to BRIL pickle files.")
parser.add_argument("--nobril", default=False, action="store_true", help="No brildata.")
parser.add_argument("--beamonly", default=False, action="store_true", help="BRIL data only has beam info.")
parser.add_argument("-q", "--queue", type=str, default="8nh", help="lxbatch queue (default:  8nh)")
parser.add_argument('-v', '--includeVertices', default=True, action="store_false", help="Include vertex counting")
parser.add_argument('--collisionType', default="pp13TeV", help="Key for xsec (default: pp13TeV)")
parser.add_argument('-o', '--outPath', default="", help="Specify the path of the output files")
parser.add_argument('--vetoListFile', default="", help="File with list of modules to veto")
parser.add_argument('-c', '--checkOutput', default=False, action="store_true", help="Only submit jobs if output is not there already.")
args=parser.parse_args()


def MakeJob(outputdir,jobid,filename,minfill):
    joblines=[]
    joblines.append("source /cvmfs/cms.cern.ch/cmsset_default.sh")
    joblines.append("cd "+outputdir)
    joblines.append("cmsenv")
    makeDataCMD="python ../makeDataCertTree.py --pccfile="+args.path+"/"+filename
    if args.nobril:
        makeDataCMD=makeDataCMD+" --nobril "
    elif args.brildir!="":
        makeDataCMD=makeDataCMD+" --brildir="+args.brildir
    makeDataCMD=makeDataCMD+" --isBatch --label="+str(jobid)+" --minfill="+str(minfill)
    if args.outPath!="":
        makeDataCMD=makeDataCMD+" --outPath="+args.outPath
    if not args.includeVertices:
        makeDataCMD=makeDataCMD+" -v"
    if args.beamonly:
        makeDataCMD=makeDataCMD+" --beamonly"
   
    makeDataCMD=makeDataCMD+" --collisionType="+args.collisionType
    makeDataCMD=makeDataCMD+" --vetoListFile="+args.vetoListFile
    #print makeDataCMD
    joblines.append(makeDataCMD)
    
    scriptFile=open(outputdir+"/job_"+str(jobid)+".sh","w+")
    for line in joblines:
        scriptFile.write(line+"\n")
        
    scriptFile.close()

def SubmitJob(job,queue="8nh"):
    baseName=str(job.split(".")[0])
    cmd="bsub -q "+queue+" -J "+baseName+" -o "+baseName+".log < "+str(job)
    output=os.system(cmd)
    if output!=0:
        print job,"did not submit properly"
        print cmd


# ls the eos directory
fileinfos=subprocess.check_output(["/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select","ls", args.path])
fileinfos=fileinfos.split("\n")

filenames={}
for fileinfo in fileinfos:
    #info=fileinfo.split()
    #if len(info)<4:
    #    continue
    #filename=info[4]
    filename=fileinfo
    if filename.find(".root") == -1:
        continue
    jobid=filename.split("/")[-1].split(".")[0].split("_")[-1]
    #print jobid, filename
    filenames[int(jobid)]=filename

fullOutPath=os.getcwd()
if not os.path.exists(args.dir):
    os.makedirs(args.dir)
fullOutPath=fullOutPath+"/"+args.dir

for job in filenames:
    MakeJob(fullOutPath,job,filenames[job],args.minfill)

if args.checkOutput:
    filesPresent=subprocess.check_output(["/afs/cern.ch/project/eos/installation/0.3.4/bin/eos.select","ls", args.outPath])
    print filesPresent


if args.sub:
    print "Submitting",len(filenames),"jobs"
    for job in filenames:
        #if job not in range(3455,3618):
        #    continue
        if args.checkOutput:
            if filesPresent.find("_"+str(job)+".root")!=-1:
                print "Found file output for job",job,"skipping"
                continue
                
        SubmitJob(args.dir+"/job_"+str(job)+".sh",args.queue)
        #raw_input()
