import json, re, subprocess
VO = {
 1: ("Ein neues Bauprojekt beginnt. | Doch was passiert mit den Bäumen, die bereits dort stehen? | Bauarbeiten können Wurzeln beschädigen, den Boden verdichten und die Bäume langfristig beeinträchtigen.", 0.80),
 2: ("Deshalb beginnt wirksamer Baumschutz nicht erst auf der Baustelle, sondern bereits bei der Planung. | Wir beurteilen mögliche Auswirkungen und entwickeln geeignete Schutzmaßnahmen.", 13.20),
 3: ("Mit geeigneten Schutzbereichen, Baumschutzzäunen und klaren Vorgaben helfen wir, Schäden an Stamm, Krone, Wurzeln und Boden zu vermeiden.", 24.80),
 4: ("Sind Eingriffe im Wurzelbereich geplant, können Wurzelsuchgrabungen erforderlich werden. | Dabei legen wir die Wurzeln möglichst schonend frei, untersuchen ihren Verlauf und schaffen eine Grundlage für die weitere Planung.", 35.60),
 5: ("Lassen sich Eingriffe nicht vollständig vermeiden, müssen geeignete Lösungen gefunden werden. | Dazu können geänderte Bauabläufe, angepasste Leitungsführungen oder ein fachgerecht hergestellter Wurzelvorhang gehören.", 49.50),
 6: ("Während der Bauarbeiten begleiten wir die Umsetzung der Schutzmaßnahmen, beraten die Beteiligten und dokumentieren relevante Eingriffe und Veränderungen.", 63.70),
 7: ("Unser Ziel: Bauvorhaben ermöglichen und wertvolle Bäume langfristig erhalten.", 73.60),
 8: ("Bischof Baumpflege. | Ihr Profi für den Baum.", 81.00),
}
def regions(f, d=0.3):
    out = subprocess.run(['ffmpeg','-v','info','-i',f,'-af',f'silencedetect=noise=-38dB:d={d}','-f','null','-'],capture_output=True,text=True).stderr
    ss=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',out)]; se=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',out)]
    dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
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
    f=f'assets/audio/vo_{i}.mp3'
    regs=regions(f)
    if len(regs)!=len(sents): print('WARN',i,len(regs),len(sents),[[round(a,2),round(b,2)] for a,b in regs])
    if len(regs)<len(sents):
        a0,b0=regs[0][0],regs[-1][1]; tot=sum(len(s) for s in sents); regs=[]; t=a0
        for s in sents: d=(b0-a0)*len(s)/tot; regs.append([t,t+d]); t+=d
    while len(regs)>len(sents):
        gaps=[regs[k+1][0]-regs[k][1] for k in range(len(regs)-1)]; k=gaps.index(min(gaps))
        regs=regs[:k]+[[regs[k][0],regs[k+1][1]]]+regs[k+2:]
    words=[]; subs=[]
    for s,(a,b) in zip(sents,regs):
        ws=s.split(); tot=sum(syl(w)+0.4 for w in ws); t=a
        for w in ws:
            d=(b-a)*(syl(w)+0.4)/tot; words.append([w,round(off+t,2),round(off+t+d,2)]); t+=d
        subs.append([s,round(off+a,2),round(off+b,2)])
    res[i]={'words':words,'subs':subs}
    print(i,[(w,s) for w,s,e in words if len(w)>7])
json.dump(res,open('src/timing.json','w'),ensure_ascii=False,indent=0)
