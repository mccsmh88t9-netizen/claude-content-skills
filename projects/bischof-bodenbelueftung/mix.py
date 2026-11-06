import subprocess
A='assets/audio/'
SH=15.05
vo=[('1.mp3',1.00),('2.mp3',11.03),('3.mp3',22.32),('4a.wav',34.23),('4b1.mp3',40.20),('4b2.mp3',46.00),('4b3.mp3',52.70),('5.mp3',46.14+SH),('6.mp3',58.90+SH)]
sfx=[('pen',0.0,0.45),('loader',1.25,0.5),('crunch',5.05,0.8),('crunch',5.6,0.6),('marker',5.75,0.5),('tick',5.24,0.35),('tick',6.3,0.3),
 ('swoosh',9.55,0.55),('tick',12.54,0.35),('marker',13.1,0.45),('bubbles',14.5,0.35),('drops',15.55,0.45),('tick',17.2,0.3),
 ('marker',21.0,0.6),('cart',21.4,0.5),('tick',23.0,0.3),('tick',25.64,0.35),('pulse',26.08,0.75),('pulse',26.70,0.65),('pulse',27.33,0.6),('marker',26.4,0.45),
 ('swoosh',33.25,0.55),('tick',35.1,0.3),('tick',36.05,0.35),('marker',36.75,0.45),('bubbles',37.2,0.35),('drops',38.0,0.4),('tick',39.85,0.3),('pen',41.6,0.35),
 ('swoosh',44.1,0.5),('tick',46.35,0.35),('marker',52.15,0.45),('swoosh',54.4,0.6),('swoosh',57.85,0.45),('chime',58.25,0.6),('marker',58.95,0.4),('tick',63.7,0.35)]
sfx=[(n,t if t<39.6 else t+SH,v) for n,t,v in sfx if not (39.6<=t<44.1)]
sfx+=[('swoosh',39.5,0.5),('tick',40.75,0.35),('tick',41.1,0.3),('marker',46.2,0.45),('tick',48.1,0.3),('tick',49.3,0.3),('drops',50.4,0.35),('swoosh',52.15,0.5),('bubbles',53.5,0.3),('drops',55.1,0.35),('tick',56.25,0.3),('marker',57.0,0.4)]
inp=['-i',A+'musik_ext.wav']+sum([['-i',A+f'vo_{n}'] for n,_ in vo],[])+sum([['-i',A+f'sfx_{s}.mp3'] for s,_,_ in sfx],[])
fc=[]
for i,(n,t) in enumerate(vo):
    fc.append(f'[{i+1}:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,volume=1.25,adelay={int(t*1000)}|{int(t*1000)}[v{i}]')
fc.append(''.join(f'[v{i}]' for i in range(len(vo)))+f'amix=inputs={len(vo)}:normalize=0,apad=whole_dur=85.05[vob]')
fc.append('[vob]asplit=2[vomix][vosc]')
for j,(s,t,v) in enumerate(sfx):
    fc.append(f'[{j+1+len(vo)}:a]aresample=48000,aformat=channel_layouts=stereo,volume={v},adelay={int(t*1000)}|{int(t*1000)}[s{j}]')
fc.append(''.join(f'[s{j}]' for j in range(len(sfx)))+f'amix=inputs={len(sfx)}:normalize=0,apad=whole_dur=85.05[sfxb]')
fc.append('[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=0.42,afade=t=in:st=0:d=0.4,afade=t=out:st=83.2:d=1.85,atrim=0:85.05[mus]')
fc.append('[mus][vosc]sidechaincompress=threshold=0.04:ratio=5:attack=40:release=450:makeup=1[musd]')
fc.append('[vomix][sfxb][musd]amix=inputs=3:normalize=0,atrim=0:85.05,loudnorm=I=-14:TP=-1.5:LRA=9[out]')
cmd=['ffmpeg','-y','-v','error']+inp+['-filter_complex',';'.join(fc),'-map','[out]','-ar','48000','-c:a','pcm_s16le','out/mix.wav']
subprocess.run(cmd,check=True); print('ok')
