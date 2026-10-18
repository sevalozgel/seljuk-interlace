import numpy as np, math
exec(open('fit.py').read().split('best=None')[0])
from scipy.spatial import cKDTree
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams['font.family']='DejaVu Serif'
S=np.load('S.npy'); q=np.load('q.npy'); qd=np.load('qdef.npy')
fig,axs=plt.subplots(1,3,figsize=(13,4.6))
img=np.asarray(im)
def segs(qq):
    P=tf(qq,centre(qq[6],qq[7],200)); return P.reshape(4*6,200,2)
for ax in axs: ax.imshow(img); ax.axis('off')
axs[0].set_title('(a) knot medallion, north iwan',fontsize=11,loc='left')
for s in segs(qd): axs[1].plot(s[:,0],s[:,1],color='#ffd400',lw=1.4)
axs[1].set_title('(b) default module, p = 0.25, h = 0.91',fontsize=11,loc='left')
for s in segs(q): axs[2].plot(s[:,0],s[:,1],color='#ffd400',lw=1.2)
P=tf(q,centre(q[6],q[7],200)); d,_=cKDTree(P).query(S)
sc=axs[2].scatter(S[:,0],S[:,1],c=d/PXCM,cmap='magma_r',s=7,vmin=0,vmax=0.6)
axs[2].set_title('(c) best fit, p = %.2f, h = %.2f'%(q[6],q[7]),fontsize=11,loc='left')
cb=fig.colorbar(sc,ax=axs[2],fraction=0.046,pad=0.02); cb.set_label('deviation of band centreline (cm)')
for ax in axs: ax.set_xlim(20,265); ax.set_ylim(275,35)
fig.tight_layout(); fig.savefig('/mnt/project-files/makale/fig8_overlay.png',dpi=200,facecolor='white')
