"""Three deterministic synthetic scenes; not real camera data or classification evidence."""
import importlib.util
from pathlib import Path

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("reference", here / "reference.py")
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
w, h = 16, 8
inputs, outputs = [], []
for pattern in range(3):
    rgb = []
    for y in range(h):
        row = []
        for x in range(w):
            if pattern == 0:
                p = (255, 30, 80) if abs(x-2*y) < 2 else (20, 170, 220)
            elif pattern == 1:
                p = (240, 180, 10) if (x//2+y//2)%2 else (10, 30, 250)
            else:
                p = ((37*x+71*y)%256, (13*x+29*y+x*y)%256, (x*x+17*y*y)%256)
            row.append((77*p[0]+150*p[1]+29*p[2]) >> 8)
            inputs.append((p[0]<<16)|(p[1]<<8)|p[2])
        rgb.append(row)
    kernel = ((1,2,1),(2,4,2),(1,2,1))
    blurred = [[sum(kernel[dy+1][dx+1]*rgb[min(h-1,max(0,y+dy))][min(w-1,max(0,x+dx))]
                    for dy in (-1,0,1) for dx in (-1,0,1)) >> 4
                for x in range(w)] for y in range(h)]
    outputs.extend(p for row in ref.crop_resize(blurred, [0,0,w-1,h-1],8,4) for p in row)
(here / "patterns_rgb.hex").write_text("".join(f"{p:06x}\n" for p in inputs))
(here / "patterns_expected.hex").write_text("".join(f"{p:02x}\n" for p in outputs))
print("PASS: generated diagonal/checker/texture 384 RGB pixels, 96 gaussian-resize golden pixels")
