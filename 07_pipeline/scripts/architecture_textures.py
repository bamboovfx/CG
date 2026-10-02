"""Author restrained 2K surface maps, preserving CC0 fabric scan originals."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
import json, hashlib

ROOT = Path('D:/00_projects/10_CG/Shot_Test')
OUT = ROOT/'02_assets/textures/authored/architecture_rebuild'
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(91126)
n = 2048

def save(name, value):
    """Save a 0..1 grayscale or RGB array as a lossless 2K PNG; return its path."""
    p = OUT/name
    Image.fromarray(np.uint8(np.clip(value, 0, 1)*255)).save(p)
    return p

def smooth(scale, blur):
    """Return seamless-ish low contrast random field at a specified source resolution."""
    im = Image.fromarray(np.uint8(rng.uniform(0,255,(scale,scale))))
    return np.asarray(im.resize((n,n),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(blur)),dtype=np.float32)/255-.5

# Paint has broad cleaning variation and submillimetre orange peel, never plaster-sized craters.
broad = smooth(24,24)
fine = smooth(640,.6)
micro = rng.normal(0,.06,(n,n)).astype(np.float32)
paint = np.clip(.82 + .035*broad + .01*fine,0,1)
save('enamel_color_2k.png',np.stack([paint,paint*.979,paint*.916],axis=2))
save('enamel_roughness_2k.png',.37+.055*broad+.045*fine+.018*micro)
save('enamel_height_2k.png',.5+.10*fine+.04*micro)
# Hairline brushing is directional at a 20 cm physical tile scale.
rows = rng.uniform(-.5,.5,(n,1)).astype(np.float32)
save('anodized_roughness_2k.png',.285+.095*rows+.025*broad+.012*micro)
save('anodized_height_2k.png',.5+.10*rows+.02*micro)
# Clear glazing is close to uniform; 2K map is intentionally barely visible.
# 16-bit storage avoids quantization bands when the door material remaps this smooth map.
Image.fromarray(np.uint16(np.clip(.038+.001*broad+.0002*micro,0,1)*65535),mode='I;16').save(OUT/'glazing_roughness_2k.png')
save('polymer_roughness_2k.png',.69+.055*fine+.024*broad)
files=[]
for p in OUT.glob('*.png'):
    files.append({'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'resolution':[2048,2048],'color_space':'sRGB' if 'color' in p.name else 'Non-Color'})
(OUT/'provenance.json').write_text(json.dumps({'method':'Deterministic authored numpy/Pillow material response, not scanned or AI generated','seed':91126,'date':'2026-09-11','paint_tile_metres':.4,'anodized_tile_metres':.2,'glazing_tile_metres':1,'files':files},indent=2),encoding='utf-8')
print('Authored',len(files),'maps')
