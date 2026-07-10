from PIL import Image
import base64, io, os

SRC = r"C:\Users\msi\Downloads"
OUT = os.path.dirname(os.path.abspath(__file__))
# map source file -> css class name, with vertical crop focus (face near top)
JOBS = {
    "screen1.png": "jm",      # Jean-Marc Dupont (homme cheveux gris)
    "screen.png":  "sk",      # Sarah Kabbaj (femme lunettes)
    "screen3.png": "ahmed",   # Ahmed B. (jeune homme tweed)
    "screen2.png": "woman2",  # Alice Martin / Aya Bennani (jeune femme)
}
SIZE = 256
total = 0
for fn, cls in JOBS.items():
    p = os.path.join(SRC, fn)
    im = Image.open(p).convert("RGB")
    w, h = im.size
    s = min(w, h)
    # center-crop square (already square, but safe)
    left = (w - s) // 2
    top = (h - s) // 2
    im = im.crop((left, top, left + s, top + s)).resize((SIZE, SIZE), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=82, optimize=True)
    b = buf.getvalue()
    b64 = base64.b64encode(b).decode("ascii")
    with open(os.path.join(OUT, f"photo_{cls}.b64"), "w") as f:
        f.write(b64)
    total += len(b64)
    print(f"{fn:14s} -> {cls:8s} {len(b):6d} bytes jpg, {len(b64):6d} b64 chars")
print(f"TOTAL b64: {total} chars (~{total/1024:.0f} Ko)")
