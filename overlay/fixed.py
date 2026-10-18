import numpy as np, math
exec(open('fit.py').read().split('best=None')[0])
from scipy.spatial import cKDTree
S=np.load('S.npy'); q=np.load('q.npy')
def c2(g,p,h): return cost(list(g)+[p,h])
for p,h in ((0.25,0.91),):
    best=None
    for rot in np.linspace(-0.4,0.4,9):
        s=107; g0=[c0[0],c0[1],s*math.cos(rot),-s*math.sin(rot),s*math.sin(rot),s*math.cos(rot)]
        r=optimize.minimize(c2,g0,args=(p,h),method='Nelder-Mead',options=dict(maxiter=4000))
        if best is None or r.fun<best.fun: best=r
    P=tf(list(best.x)+[p,h],centre(p,h,200)); d1,_=cKDTree(P).query(S)
    print(p,h,'photo->model mean %.2f cm p90 %.2f'%(d1.mean()/PXCM,np.percentile(d1,90)/PXCM))
    np.save('qdef.npy',np.array(list(best.x)+[p,h]))
