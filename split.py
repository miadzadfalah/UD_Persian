import sys
import codecs
import re
import os

SCRIPTDIR=os.path.dirname(os.path.abspath(__file__))

out8=codecs.getwriter("utf-8")(sys.stdout)

def read_conll(inp,maxsent):
    """ Read conll format file and yield one sentence at a time as a list of lists of columns. If inp is a string it will be interpreted as filename, otherwise as open file for reading in unicode"""
    if isinstance(inp,basestring):
        f=codecs.open(inp,u"rt",u"utf-8")
    else:
        f=codecs.getreader("utf-8")(sys.stdin) # read stdin
    count=0
    sent=[]
    comments=[]
    for line in f:
        line=line.strip()
        if not line:
            if sent:
                count+=1
                yield sent, comments
                if maxsent!=0 and count>=maxsent:
                    break
                sent=[]
                comments=[]
        elif line.startswith(u"#"):
            if sent:
                raise ValueError("Missing newline after sentence")
            comments.append(line)
            continue
        else:
            sent.append(line.split(u"\t"))
    else:
        if sent:
            yield sent, comments

    if isinstance(inp,basestring):
        f.close() #Close it if you opened it

split_re=re.compile(ur"(/|\\)",re.U)
def parts(deprel):
    deps=split_re.split(deprel)
    if len(deps)==3: #all but one case!
        if deps[1]==u"/":
            return deps[0],deps[2],"RIGHT"
        elif deps[1]==u"\\":
            return deps[0],deps[2],"LEFT"
        else:
            assert False, deps
    else:
        return [deprel] #no-op

ID,FORM,LEMMA,CPOS,POS,FEAT,HEAD,DEPREL,DEPS,MISC=range(10)
def split_clitics(sent,comments):
    new_sent=[]
    tokens=[] #list of words that initiate a two-word token
    offsets=[0 for _ in sent]
    counter=0
    for idx,line in enumerate(sent):
        assert len(line)==10
        counter+=1
        deps=parts(line[DEPREL])
        if len(deps)==1: #nothing to do
            new_sent.append(line)
            continue
        else:
            #Need to split
            #comments.append(u"###TOKEN###%d-%d\t%s"%(int(line[0]),int(line[0]+1),line[1])+(u"\t_"*7))
            new_sent.append(line[:])
            new_sent[-1][ID]=unicode(counter)
            counter+=1
            new_sent.append(line[:])
            new_sent[-1][ID]=unicode(counter)
            for idx in range(int(line[ID])+1,len(sent)):
                offsets[idx]+=1
            if deps[2]=="LEFT":
                new_sent[-2][DEPREL]=deps[0]
                new_sent[-1][DEPREL]=u"SPLTL:"+deps[1]
                new_sent[-1][HEAD]=line[ID]
                new_sent[-1][FORM]=u"???"
                new_sent[-1][FEAT]=u"_"
            elif deps[2]=="RIGHT":
                new_sent[-1][DEPREL]=deps[0]
                new_sent[-2][DEPREL]=u"SPLTR:"+deps[1]
                new_sent[-2][HEAD]=unicode(int(line[ID])+1)
                new_sent[-2][FORM]=u"???"
                new_sent[-2][FEAT]=u"_"

    #Renumber all heads
    for idx,l in enumerate(new_sent):
        if l[HEAD]!=u"0":
            l[HEAD]=unicode(int(l[HEAD])+offsets[int(l[HEAD])-1])
        l[ID]=unicode(idx+1)
    return new_sent
            
if __name__=="__main__":
    for sent,comments in read_conll(sys.stdin,0):
        sent=split_clitics(sent,comments)
        if comments:
            print >> out8, u"\n".join(comments)
        print >> out8, u"\n".join(u"\t".join(l) for l in sent)
        print >> out8


        
        
