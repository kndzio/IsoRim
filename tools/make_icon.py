from PIL import Image, ImageDraw, ImageFilter
S=4; N=128*S
img=Image.new('RGBA',(N,N),(0,0,0,0)); d=ImageDraw.Draw(img)
# rounded tile background, dusk gradient
bg=Image.new('RGBA',(N,N)); bd=ImageDraw.Draw(bg)
for y in range(N):
    t=y/N; bd.line([(0,y),(N,y)],fill=(int(38+30*t),int(52+28*t),int(66+10*t),255))
mask=Image.new('L',(N,N),0); ImageDraw.Draw(mask).rounded_rectangle([4*S,4*S,N-4*S,N-4*S],radius=22*S,fill=255)
img.paste(bg,(0,0),mask); d=ImageDraw.Draw(img)
cx,cy=N/2,N*0.56; u=21*S
def P(x,y,z): return (cx+(x-y)*u*0.866, cy+(x+y)*u*0.5-z*u)
def poly(pts,col): d.polygon([P(*p) for p in pts],fill=col)
# grass tile
g=1.65
poly([(-g,-g,0),(g,-g,0),(g,g,0),(-g,g,0)],(118,140,92,255))
poly([(-g,g,0),(g,g,0),(g,g,-0.35),(-g,g,-0.35)],(84,72,56,255))
poly([(g,-g,0),(g,g,0),(g,g,-0.35),(g,-g,-0.35)],(104,88,66,255))
# water pool corner
poly([(1.0,-g,0.001),(g,-g,0.001),(g,-0.2,0.001),(1.3,-0.6,0.001)],(78,120,124,255))
# house walls
w,h=0.95,1.0
poly([(-w,w,0),(w,w,0),(w,w,h),(-w,w,h)],(196,178,150,255))   # front-left face
poly([(w,-w,0),(w,w,0),(w,w,h),(w,-w,h)],(160,142,118,255))   # front-right face
# door
poly([(-0.2,w+0.001,0),(0.25,w+0.001,0),(0.25,w+0.001,0.6),(-0.2,w+0.001,0.6)],(92,66,46,255))
# window
poly([(w+0.001,-0.45,0.45),(w+0.001,0.15,0.45),(w+0.001,0.15,0.8),(w+0.001,-0.45,0.8)],(232,206,120,255))
# hipped roof
o=1.15; r=h+0.95; rx=0.25
poly([(-o,o,h),(o,o,h),(rx,0,r),(-rx,0,r)],(176,92,64,255))
poly([(-o,-o,h),(o,-o,h),(rx,0,r),(-rx,0,r)],(150,76,54,255))
poly([(o,-o,h),(o,o,h),(rx,0,r)],(140,70,50,255))
poly([(-o,-o,h),(-o,o,h),(-rx,0,r)],(196,108,76,255))
# tree
tx,ty=-1.25,0.9
poly([(tx-0.08,ty,0),(tx+0.08,ty,0),(tx+0.08,ty,0.5),(tx-0.08,ty,0.5)],(96,70,50,255))
for (z,rad,col) in [(0.55,0.42,(70,108,64,255)),(0.95,0.32,(86,126,74,255)),(1.25,0.2,(100,140,84,255))]:
    a=P(tx,ty,z+rad*0.9); b=P(tx,ty,z)
    d.polygon([a,(b[0]-rad*u,b[1]),(b[0],b[1]+rad*u*0.35),(b[0]+rad*u,b[1])],fill=col)
# outline glow
img=img.resize((128,128),Image.LANCZOS)
import sys; img.save(sys.argv[1])
img.resize((512,512),Image.NEAREST).save('icon_big.png')
