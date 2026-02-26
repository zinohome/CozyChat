import subprocess
import os

tracks = [
    ("1.mp3", "synth 600 brownnoise band -n 1200 200 tremolo 0.1 43"), # 海浪
    ("2.mp3", "synth 600 pinknoise band -n 2500 500 tremolo 1 10"),   # 林地
    ("3.mp3", "synth 600 sine 432 sine 436 mix synth 600 sine 216 vol 0.5"), # 星空
    ("4.mp3", "synth 600 whitenoise band -n 1000 500 tremolo 10 30"), # 细雨
    ("5.mp3", "synth 600 sine %-12 sine %-9 sine %-5 synth 600 pinknoise mix"), # 云端
    ("6.mp3", "synth 600 brownnoise synth 600 sine 300 mix band -n 800 200"), # 小溪
    ("7.mp3", "synth 600 sine 528 synth 600 sine 532 mix"), # 悠然
    ("8.mp3", "synth 600 whitenoise band -n 5000 1000 tremolo 5 50"), # 蝉鸣
    ("9.mp3", "synth 600 sine 432 synth 600 sine 864 mix tremolo 0.5 20"), # 极光
    ("10.mp3", "synth 600 brownnoise band -n 300 100 reverb 100") # 远山
]

for filename, spec in tracks:
    print(f"Generating {filename}...")
    cmd = f"sox -n -r 44100 -c 2 {filename} {spec}"
    subprocess.run(cmd, shell=True)

print("Done")
