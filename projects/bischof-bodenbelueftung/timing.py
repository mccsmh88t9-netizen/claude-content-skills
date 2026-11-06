import json, re, subprocess
VO = {
 1: ("Schwere Baufahrzeuge können den Boden im Wurzelbereich von Bäumen stark verdichten. | Doch was bedeutet das eigentlich für den Baum?", 1.00),
 2: ("Durch die Verdichtung wird der Porenraum verkleinert. | Der Gasaustausch und die Wasserbewegung können beeinträchtigt werden. | Das erschwert die Lebensbedingungen der Baumwurzeln.", 11.03),
 3: ("Mit unserem VOGT Geo Injector Maxi bringen wir gezielt Druckluftimpulse in den Boden ein. | Damit sollen verdichtete Bodenbereiche gelockert und die Standortbedingungen verbessert werden.", 22.32),
 4: ("Ziel der Behandlung ist es, die Bodenstruktur und den Gasaustausch zu verbessern. | Je nach Standort können zusätzlich geeignete Bodenhilfsstoffe eingebracht werden.", 34.23),
 5: ("Ein funktionsfähiger Boden ist eine wichtige Voraussetzung für gesunde Wurzeln – | und für die langfristige Entwicklung unserer Bäume.", 46.14),
 6: ("Bischof Baumpflege. | Ihr Profi für den Baum.", 58.90),
}
def regions(f):
    out = subprocess.run(['ffmpeg','-v','info','-i',f,'-af','silencedetect=noise=-38dB:d=0.18','-f','null','-'],capture_output=True,text=True).stderr
    ss=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',out)]; se=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',out)]
    dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
    # speech start: first non-silent; assume ~0.05
    st=0.05; regs=[]
    for a,b in zip(ss,se):
        if a-st>0.3: regs.append([st,a])
        st=b
    if dur-st>0.3: regs.append([st,dur-0.05])
    return regs
def syl(w): return max(1,len(re.findall(r'[aeiouäöüy]+',w.lower())))
res={}
for i,(txt,off) in VO.items():
    sents=[s.strip() for s in txt.split('|')]
    regs=regions(f'assets/audio/vo_{i}.mp3')
    if len(regs)!=len(sents): print('WARN',i,len(regs),len(sents),regs)
    regs=regs[:len(sents)]
    words=[]; subs=[]
    for s,(a,b) in zip(sents,regs):
        ws=s.split(); tot=sum(syl(w)+0.4 for w in ws); t=a
        for w in ws:
            d=(b-a)*(syl(w)+0.4)/tot; words.append([w,round(off+t,2),round(off+t+d,2)]); t+=d
        subs.append([s,round(off+a,2),round(off+b,2)])
    res[i]={'words':words,'subs':subs}
    print(i,[ (w,s) for w,s,e in words if len(w)>6])
json.dump(res,open('src/timing.json','w'),ensure_ascii=False,indent=0)
