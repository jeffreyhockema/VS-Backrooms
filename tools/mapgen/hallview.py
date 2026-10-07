# Overlays Level 0 hallways (hall.bin from L0HALL=1 mapgen) on map.png and crops: python hallview.py x0 z0 width scale out.png
import sys
from PIL import Image
x0,z0,w,scale=[int(a) for a in sys.argv[1:5]]
im=Image.open('map.png').convert('RGB'); px=im.load()
size=im.size[0]; hb=open('hall.bin','rb').read()
for z in range(size):
  for x in range(size):
    h=hb[z*size+x]
    if h:
      r,g,b=px[x,z]; px[x,z]=(int(r*0.55),int(g*0.75)+40,int(b*0.55)+60)
im.crop((x0,z0,x0+w,z0+w)).resize((w*scale,w*scale),Image.NEAREST).save(sys.argv[5])
