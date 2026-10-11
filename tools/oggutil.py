"""Writing OGG Vorbis sounds so that running a generator again leaves the sounds it did not change alone.

libsndfile gives every Ogg stream a random serial number, so the same signal encodes to different bytes on every run,
and every sound a generator writes would show as changed in git. write_ogg encodes to a temporary file beside the
target and keeps the old file when the two differ only in the serial numbers (and the page checksums, which cover
them). It also feeds the encoder a quarter of a second at a time: libsndfile can crash when asked to encode a long
Vorbis buffer in one call.
"""
import os

import numpy as np
import soundfile as sf


def _without_serials(data):
    """The Ogg pages with each page's stream serial number and checksum zeroed."""
    out = bytearray(data)
    i = 0
    while i + 27 <= len(out) and out[i:i + 4] == b"OggS":
        out[i + 14:i + 18] = b"\0\0\0\0"   # bitstream serial number
        out[i + 22:i + 26] = b"\0\0\0\0"   # CRC, which covers the serial
        segments = out[i + 26]
        i += 27 + segments + sum(out[i + 27:i + 27 + segments])
    return bytes(out)


def write_ogg(path, signal, rate):
    """Writes a mono signal to path as OGG Vorbis, unless the file there already holds the same encoding.
    Returns True if the file was written."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    signal = np.asarray(signal, dtype=np.float32)
    tmp = path + ".tmp"
    with sf.SoundFile(tmp, "w", samplerate=rate, channels=1, format="OGG", subtype="VORBIS") as f:
        for start in range(0, len(signal), rate // 4):
            f.write(signal[start:start + rate // 4])
    if os.path.exists(path):
        with open(path, "rb") as old, open(tmp, "rb") as new:
            same = _without_serials(old.read()) == _without_serials(new.read())
        if same:
            os.remove(tmp)
            return False
    os.replace(tmp, path)
    return True
