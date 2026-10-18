import numpy as np, math
exec(open('fit.py').read().split('best=None')[0])
from scipy.spatial import cKDTree
q=np.load('q.npy')
DTin=ndimage.distance_transform_edt(dark)
mx=ndimage.maximum_filter(DTin,size=5)
sk=(DTin>=mx-0.01)&(DTin>=2.5)
S=np.argwhere(sk)[:,::-1].astype(float)
P=tf(q,centre(q[6],q[7],200))
d1,_=cKDTree(P).query(S); d2,_=cKDTree(S).query(P)
print('n skel',len(S))
for name,d in (('photo->model',d1),('model->photo',d2)):
    print(name,'mean %.2f cm  median %.2f  p90 %.2f'%(d.mean()/PXCM,np.median(d)/PXCM,np.percentile(d,90)/PXCM))
print('band width (2*median DTin on skel) cm', 2*np.median(DTin[sk])/PXCM)
np.save('S.npy',S); np.save('d1.npy',d1)
