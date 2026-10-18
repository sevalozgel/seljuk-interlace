import numpy as np, math
from PIL import Image
from scipy import ndimage, optimize
SRC='/root/.claude/uploads/06f9fb29-83b8-55ee-a2b7-37b3609ce632/e391ceae-image.jpg'
box=(100,120,400,420); PXCM=15.25
im=Image.open(SRC).convert('RGB').crop(box); A=np.asarray(im).astype(float)
hsv=np.asarray(im.convert('HSV')).astype(float)
dark=(hsv[...,2]<85)
H,W=dark.shape; yy,xx=np.mgrid[0:H,0:W]
c0=np.array([142.,155.]); roi=((xx-c0[0])**2+(yy-c0[1])**2)<118**2
dark&=roi
dark=ndimage.binary_opening(dark,iterations=1)
# skeleton-ish: use dark pixels themselves
DT=ndimage.distance_transform_edt(~dark)
def centre(p,h,n=60):
    a=p; s=h; pts=[]
    loop=[(a,-s),(a,s),(0,1),(-a,s),(-a,-s),(0,-1),(a,-s)]
    for k in range(4):
        t=k*math.pi/4; ct,st=math.cos(t),math.sin(t)
        for i in range(6):
            (x0,y0),(x1,y1)=loop[i],loop[i+1]
            for u in np.linspace(0,1,n,endpoint=False):
                x=x0+(x1-x0)*u; y=y0+(y1-y0)*u
                pts.append((x*ct-y*st,x*st+y*ct))
    return np.array(pts)
def tf(q,P):
    tx,ty,a,b,c,d=q[:6]
    M=np.array([[a,b],[c,d]]); return P@M.T+[tx,ty]
dpts=np.argwhere(dark)[:,::-1].astype(float)
def cost(q,ret=False):
    p,h=q[6],q[7]
    P=tf(q,centre(p,h))
    xi=np.clip(P[:,0].round().astype(int),0,W-1); yi=np.clip(P[:,1].round().astype(int),0,H-1)
    m2p=DT[yi,xi]
    # photo->model
    from scipy.spatial import cKDTree
    tr=cKDTree(P); p2m,_=tr.query(dpts)
    if ret: return m2p,p2m,P
    return m2p.mean()+0.5*np.mean(np.minimum(p2m,15))
best=None
for rot in np.linspace(-0.4,0.4,9):
  for p in (0.2,0.25,0.3):
    for h in (0.8,0.9):
      s=107; q0=[c0[0],c0[1],s*math.cos(rot),-s*math.sin(rot),-s*math.sin(rot)*-1,s*math.cos(rot),p,h]
      q0=[c0[0],c0[1],s*math.cos(rot),-s*math.sin(rot),s*math.sin(rot),s*math.cos(rot),p,h]
      r=optimize.minimize(cost,q0,method='Nelder-Mead',options=dict(maxiter=4000,xatol=1e-3,fatol=1e-4))
      if best is None or r.fun<best.fun: best=r
q=best.x; m2p,p2m,P=cost(q,True)
M=np.array([[q[2],q[3]],[q[4],q[5]]]); U,S,Vt=np.linalg.svd(M)
print('cost',best.fun,'p,h',q[6],q[7],'sv',S,'R_cm',S.mean()/PXCM)
print('model->photo mean %.2f px = %.2f cm, 90pct %.2f cm'%(m2p.mean(),m2p.mean()/PXCM,np.percentile(m2p,90)/PXCM))
# band half-width approx: dark band centre deviation: compute centreline dist via skeleton
np.save('q.npy',q)
