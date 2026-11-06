import sys, numpy as np
from PIL import Image
from scipy import ndimage as nd
def cut(path):
    im=Image.open(path).convert('RGB'); a=np.array(im).astype(float)
    bg=np.median(np.concatenate([a[:8].reshape(-1,3),a[-8:].reshape(-1,3),a[:,:8].reshape(-1,3),a[:,-8:].reshape(-1,3)]),0)
    dist=np.sqrt(((a-bg)**2).sum(2))
    near=dist<22
    lab,n=nd.label(near)
    border=set(np.unique(np.concatenate([lab[0],lab[-1],lab[:,0],lab[:,-1]])))-{0}
    bgmask=np.isin(lab,list(border))
    # also enclosed small background pockets (between legs/arms): large near-regions with low dist
    sizes=nd.sum(near,lab,range(n+1))
    for i in range(1,n+1):
        if i not in border and sizes[i]>4000:
            m=lab==i
            if dist[m].mean()<9: bgmask|=m
    fg=~bgmask
    fg=nd.binary_closing(fg,iterations=2)
    soft=nd.gaussian_filter(fg.astype(float),0.8)
    # edge pixels: alpha from distance to bg too
    alpha=np.where(fg, 1.0, 0)*1.0
    alpha=np.clip(np.maximum(soft*0.0+alpha*soft, 0),0,1)
    alpha=np.where(bgmask&(dist>6), np.clip(dist/40,0,1)*soft, alpha)
    out=np.dstack([a,alpha*255]).astype(np.uint8)
    return Image.fromarray(out,'RGBA'), fg
def objects(img, fg, minarea=20000, pad=12):
    lab,n=nd.label(nd.binary_dilation(fg,iterations=14))
    objs=nd.find_objects(lab); res=[]
    for i,sl in enumerate(objs):
        if sl is None: continue
        area=(lab[sl]==i+1).sum()
        if area<minarea: continue
        y0,y1=max(0,sl[0].start-pad),sl[0].stop+pad; x0,x1=max(0,sl[1].start-pad),sl[1].stop+pad
        res.append((y0,x0,img.crop((x0,y0,x1,y1))))
    return res
if __name__=='__main__':
    src,prefix=sys.argv[1],sys.argv[2]
    img,fg=cut(src)
    objs=objects(img,fg)
    objs.sort(key=lambda o:(round(o[0]/400),o[1]))
    for k,(y,x,o) in enumerate(objs):
        o.save(f'{prefix}_{k+1}.png'); print(prefix,k+1,o.size,(x,y))
