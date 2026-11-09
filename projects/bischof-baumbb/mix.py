import subprocess, json
A='assets/audio/'
T=json.load(open('src/timing.json'))
def W(n,w):
    for x in T[str(n)]['words']:
        if x[0].strip('.,–?:').startswith(w): return x[1]
    return 0
vo=[(f'vo_{n}.mp3',T[str(n)]['subs'][0][1]-0.05 if False else off) for n,off in [(1,0.8),(2,13.2),(3,24.8),(4,35.6),(5,49.5),(6,63.7),(7,73.6),(8,81.0)]]
sfx=[('pen',0.0,0.4),('tick',3.2,0.3),('marker',1.25,0.35),('excavator',5.3,0.1),('tick',W(1,'Bauarbeiten')-0.1,0.35),('crunch',W(1,'verdichten')-0.1,0.45),('marker',W(1,'Wurzeln')+0.2,0.4),
 ('rewind',12.3,0.55),('swoosh',13.55,0.5),
 ('tick',W(2,'Baumschutz')-0.1,0.3),('tick',15.0,0.3),('marker',W(2,'beurteilen')-0.3,0.4),('marker',W(2,'mögliche')-0.1,0.45),('tick',W(2,'Auswirkungen')+0.1,0.4),('pen',W(2,'entwickeln')-0.1,0.35),('marker',24.2,0.55),
 ('tick',W(3,'Schutzbereichen')-0.2,0.3),('fence',W(3,'Schutzbereichen'),0.5),('fence',W(3,'Baumschutzzäunen')+0.2,0.45),('loader',25.2,0.1),('tick',W(3,'Vorgaben')-0.6,0.3),('tick',W(3,'Boden')-0.9,0.3),('swoosh',34.95,0.55),
 ('tick',W(4,'geplant')-0.3,0.3),('tick',W(4,'Wurzelsuchgrabungen')-0.1,0.3),('trowel',W(4,'erforderlich')+0.3,0.5),('trowel',W(4,'erforderlich')+2.2,0.45),('tick',W(4,'untersuchen')+0.1,0.35),('tick',W(4,'Grundlage')-0.3,0.3),
 ('tick',W(5,'Eingriffe')-0.1,0.3),('tick',W(5,'geänderte')-0.25,0.3),('tick',W(5,'angepasste')+0.15,0.3),('marker',W(5,'Leitungsführungen')-0.1,0.4),('swoosh',59.2,0.5),('pen',59.9,0.35),
 ('swoosh',63.4,0.5),('tick',W(6,'begleiten')-0.1,0.3),('marker',W(6,'Schutzmaßnahmen')-0.4,0.4),('tick',W(6,'beraten')-0.1,0.3),('shutter',W(6,'dokumentieren')+0.25,0.7),('tick',W(6,'dokumentieren')+0.55,0.3),
 ('swoosh',73.4,0.45),('pen',74.6,0.35),('tick',W(7,'Bauvorhaben')-0.2,0.3),('marker',W(7,'langfristig')-0.2,0.4),('swoosh',79.3,0.5),('chime',79.6,0.6),('marker',W(8,'Bischof'),0.4)]
DUR=89.0
inp=['-i',A+'musik.mp3']+sum([['-i',A+f] for f,_ in vo],[])+sum([['-i',A+f'sfx_{s}.'+('wav' if s=='rewind' else 'mp3')] for s,_,_ in sfx],[])
fc=[]
for i,(f,t) in enumerate(vo):
    fc.append(f'[{i+1}:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,volume=1.25,adelay={int(t*1000)}|{int(t*1000)}[v{i}]')
fc.append(''.join(f'[v{i}]' for i in range(len(vo)))+f'amix=inputs={len(vo)}:normalize=0,apad=whole_dur={DUR}[vob]')
fc.append('[vob]asplit=2[vomix][vosc]')
for j,(s,t,v) in enumerate(sfx):
    fc.append(f'[{j+1+len(vo)}:a]aresample=48000,aformat=channel_layouts=stereo,volume={v},adelay={int(t*1000)}|{int(t*1000)}[s{j}]')
fc.append(''.join(f'[s{j}]' for j in range(len(sfx)))+f'amix=inputs={len(sfx)}:normalize=0,apad=whole_dur={DUR}[sfxb]')
fc.append(f'[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.4,afade=t=in:st=0:d=0.4,afade=t=out:st={DUR-2.2}:d=2.2,atrim=0:{DUR}[mus]')
fc.append('[mus][vosc]sidechaincompress=threshold=0.04:ratio=5:attack=40:release=450:makeup=1[musd]')
fc.append(f'[vomix][sfxb][musd]amix=inputs=3:normalize=0,atrim=0:{DUR},loudnorm=I=-14:TP=-1.5:LRA=9[out]')
subprocess.run(['ffmpeg','-y','-v','error']+inp+['-filter_complex',';'.join(fc),'-map','[out]','-ar','48000','-c:a','pcm_s16le','out/mix.wav'],check=True); print('ok')
