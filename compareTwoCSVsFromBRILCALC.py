import sys
import ROOT



def dictFromCSVFile(file):
    lines=file.readlines()
    dict={}

    for line in lines:
        try:
            #254231:4201,1:1,1439442880,STABLE BEAMS,6500,1357.453,1338.269,0.0,DT
            items=line.replace(':',',').split(",")
            #print items
            #print items[1],items[0],items[2],items[9]
            
            dict[(int(items[1]),int(items[0]),int(items[2]))]=[int(items[4]),float(items[8])]
        except:
            print "can't parse",line
            print items
            pass

    return dict

filename1=sys.argv[1]
filename2=sys.argv[2]

nLS=10

file1=open(filename1)
file2=open(filename2)

dict1=dictFromCSVFile(file1)
dict2=dictFromCSVFile(file2)

overtlapKeys=list(set(dict1).intersection(dict2))
overtlapKeys.sort()

print len(dict1),len(dict2),len(overtlapKeys)

can=ROOT.TCanvas("can","",700,700)
ratio=ROOT.TH1F("ratio",";ratio "+filename2+"/"+filename1+";",200,0,2)
ratioNarrow=ROOT.TH1F("ratioNarrow",";ratio "+filename2+"/"+filename1+";",200,0.9,1.1)
ratioVsTime=ROOT.TGraph()
ratioVsInst=ROOT.TGraph()

baddies={}
iCount=0
num=0
den=0
for key in overtlapKeys:
    try:
        num=num+dict2[key][1]
        den=den+dict1[key][1]
        if iCount%10==9:
            ratio.Fill(num/den)
            ratioNarrow.Fill(num/den)
            ratioVsTime.SetPoint(iCount,dict1[key][0],num/den)
            ratioVsInst.SetPoint(iCount,den/10,num/den)
            num=0
            den=0
            
        iCount=iCount+1
        if abs(1-dict1[key][1]/dict2[key][1])>.03:
            #print key,dict1[key],dict2[key],1-dict2[key]/dict1[key]
            newKey=(key[0],key[1])
            print key
            if newKey not in baddies:
                baddies[newKey]=1
            else:
                baddies[newKey]=baddies[newKey]+1

    except:
        print "fail",key
        pass

badkeys=baddies.keys()
badkeys.sort()
for key in badkeys:
    if  baddies[key]>10:
        print key, baddies[key]

ratioVsInst.Draw("AP")
can.Update()
raw_input()
ratio.Draw()
can.Update()
raw_input()
ratioNarrow.Draw()
ratioNarrow.Fit("gaus")
can.Update()
raw_input()
ratioVsTime.Draw("AP")
can.Update()
raw_input()
