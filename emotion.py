from ctypes import CDLL, c_char_p
import os

lib_path = os.path.abspath(r"./core/target/release/emotion.dll")
lib = CDLL(lib_path)
lib.analyze_emotion.restype = c_char_p

def analyze_emotion(text: str) -> str:
    resultado = lib.analyze_emotion(text.encode("utf-8"))
    return resultado.decode("utf-8")
