# Verbesserte Freistellung: nur außen zusammenhängender Hintergrund wird entfernt,
# eingeschlossene helle Flächen (Plan, Papier) bleiben deckend; Kante 1px eingezogen und entsäumt.
import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
def cut(src, prefix, target_h=800, gap_min=6000):
    im=Image.open(src).convert('RGB'); a=np.array(im).astype(float)
    bg=np.median(np.concatenate([a[:8].reshape(-1,3),a[-8:].reshape(-1,3),a[:,:8].reshape(-1,3),a[:,-8:].reshape(-1,3)]),0)
    dist=np.sqrt(((a-bg)**2).sum(2))
    near=dist<20
    lab,n=nd.label(near)
    border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    bgm=np.isin(lab,list(border))
    # große, sehr hintergrundnahe Lücken (z. B. zwischen Arm und Körper) ebenfalls entfernen,
    # aber nur wenn sie praktisch keine Zeichnung enthalten (Papier/Plan bleibt)
    sizes=nd.sum(near,lab,range(n+1))
    for i in range(1,n+1):
        if i in border or sizes[i]<gap_min: continue
        m=lab==i
        if dist[m].mean()<4.5 and dist[m].std()<3.5: bgm|=m
    fg=nd.binary_fill_holes(~bgm) & ~bgm | (~bgm)
    fg=nd.binary_opening(fg,iterations=1)
    fg=nd.binary_erosion(fg,iterations=1)
    alpha=nd.gaussian_filter(fg.astype(float),0.7)
    # Entsäumen: Hintergrundfarbe aus halbtransparenten Kantenpixeln herausrechnen
    al=np.clip(alpha,1e-3,1)[...,None]
    col=np.where(al<0.999,(a-bg*(1-al))/al,a); col=np.clip(col,0,255)
    out=np.dstack([col,alpha*255]).astype(np.uint8)
    img=Image.fromarray(out,'RGBA')
    labo,no=nd.label(nd.binary_dilation(fg,iterations=14))
    objs=[]
    for k,sl in enumerate(nd.find_objects(labo)):
        if sl is None: continue
        if (labo[sl]==k+1).sum()<20000: continue
        y0,y1=max(0,sl[0].start-12),sl[0].stop+12; x0,x1=max(0,sl[1].start-12),sl[1].stop+12
        crop=np.array(img.crop((x0,y0,x1,y1)))
        # nur die Hauptfigur im Ausschnitt behalten
        m=crop[...,3]>20; l2,n2=nd.label(nd.binary_dilation(m,iterations=5)); s2=nd.sum(m,l2,range(n2+1))
        keep=np.isin(l2,[j for j in range(1,n2+1) if s2[j]>0.1*s2.max()]); crop[...,3]=np.where(keep,crop[...,3],0)
        objs.append((y0,x0,Image.fromarray(crop)))
    objs.sort(key=lambda o:(round(o[0]/400),o[1]))
    for k,(y,x,o) in enumerate(objs):
        if o.size[1]>target_h: o=o.resize((round(o.size[0]*target_h/o.size[1]),target_h),Image.LANCZOS)
        o.save(f'{prefix}_{k+1}.png',optimize=True); print(prefix,k+1,o.size)
if __name__=='__main__': cut(sys.argv[1],sys.argv[2])
