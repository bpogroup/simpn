import base64
import hashlib

def convert_image_to_base64(fname):
    with open(fname, "rb") as f:
        encoded = base64.b64encode(f.read())
        with open(fname + ".b64", "wb") as fout:
            fout.write(encoded)
        print(hashlib.md5(encoded).hexdigest())

convert_image_to_base64("./assets/data/play.png")