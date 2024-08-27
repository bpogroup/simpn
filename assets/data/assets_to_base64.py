import base64
import hashlib

fname = "./assets/data/logo.png"
with open(fname, "rb") as f:
    encoded = base64.b64encode(f.read())
    with open(fname + ".b64", "wb") as fout:
        fout.write(encoded)
    print(hashlib.md5(encoded).hexdigest())
