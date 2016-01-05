# Certification Instructions

DataCert is weekly certification of luminosity for CMS data  
VdmPrep is for producing vdm mini-trees for the VdM framework


Below are examples of how to use the data certification scripts.  The goal is to 
efficiently go from PCCNtuples to an intermediate flat tree (certtree) and finally 
to series of luminosity plots per CMS run number.


All files take arguments using parser (-o option or --myoption=option syntax).  For 
all of them you can do:
python my.py -h
for help understanding options.


###makeDummyJSON.py
Produces a json file with runs given as input and an excessive luminosity section 
range that will cover all the LSs in a single run.  Very simple script.  Usage:

python makeDummyJSON.py run1 run2 ... runN
Output:  jsondummy_run1_runN.txt


###retrieveBRILData.py
This is a wrapper script for brilcalc.  It produces a pickle file with the brildata 
which will be read by makeDataCertTree.py.  The usage is below.  Make sure to use 
"-o" to overwrite (the checking algorithm isn't working right for json files).

source brilcalc_env.sh
python retrieveBRILData.py -j jsondummy_run1_runN.txt -o


###makeDataCertTree.py
This script makes takes input from pcc ntuples and the pickled brildata files 
originating from brilcalc.  The basic use of this script takes the pcc file and the 
directory where the brilcalc pickle files are located.  There are several features 
which should be useful:  setting the minimum LHC fill number for instance.

E.g.
python makeDataCertTree.py --pccfile=/store/user/capalmer/ZeroBias1/PCC_Zerobias1_RunCert_0Bfield_LStest2/150626_191443/0000/pcc_Data_LS_12.root --brildir=brildata

E.g.  (BRIL only output)
python makeDataCertTree.py --brildir=brildata -l BRILONLY
Output:  dataCertification_254227_254332_BRILONLY.root



###mkAndSubmitJobs.py
Most of the time you will use this script as a wrapper for makeDataCertTree.py.

E.g.
python mkAndSubmitJobs.py -p /store/user/capalmer/ZeroBias1/PCC_Zerobias1_RunCert_0Bfield_LStest2/150626_191443/0000 -d MyJobsGoInThisDir -s

-s will submit your jobs to the queue as well.  The default is to NOT submit the 
jobs but just create the job_\#\.sh files in MyJobsGoInThisDir.  When submitting 
the jobs batch-wise only run,LS entries with CMS and BRIL data are saved (-b option).



###hadd step
After successfully getting all the output back from your jobs. You need to (by 
hand) hadd the root files:
E.g.
hadd dataCertification_246908_248038_merged.root MyJobsGoInThisDir/dataCertification_246908_248038_\*.root



###createJSONOfRunLS.py
Only entries with both CMS and BRIL data are saved here.  You need to add run,LS 
entries where there are no pixel clusters and only BRIL luminometers have provided 
data.  Using this script is the first step in that process.  It reads all the 
run,LS entries in a root file and writes a JSON file in the typical CMS format:
E.g.
python createJSONOfRunLS.py -f FullTest/dataCertification_246908_248038_merged.root -l LABEL
Output:  jsonOfReadRunLSsLABEL.txt



###filterOutJSON.py
This takes a JSON file and a certtree.  If the run,LS pair of an entry in the tree 
is NOT in the JSON file, then the entry will be saved exactly in a new tree.
E.g.
python filterOutJSON.py -r dataCertification_246908_248038_BRILONLY.root -j jsonOfReadRunLSsLABEL.txt
Output:  dataCertification_246908_248038_BRILONLY_filtered.root



###hadd CMS+BRIL tree with filtered BRILONLY tree
hadd -f dataCertification_246908_248038_complete.root dataCertification_246908_248038_merged.root dataCertification_246908_248038_BRILONLY_filtered.root



###dataCertPlots.py
To look in the tree and auto generate a list of runs use -a:
E.g.
python dataCertPlots.py -b -c dataCertification_246908_248038_all.root -a

Otherwise give a comma separated (NO SPACES) list with -r:
E.g.
python dataCertPlots.py -b -c dataCertification_246908_248038_all.root -r 246908,248038



