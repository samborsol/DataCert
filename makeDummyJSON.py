import sys

runs=sys.argv[1:]
jsonfile=open("jsondummy_"+str(runs[0])+"_"+str(runs[-1])+".txt","w")
jsonfile.write("{")

for run in runs:
    if run is runs[-1]:
        jsonfile.write("\""+str(run)+"\": [[0,999999]]\n")  
    else:
        jsonfile.write("\""+str(run)+"\": [[0,999999]],\n")  

jsonfile.write("}\n")
jsonfile.close()
