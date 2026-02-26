import urllib.request
import os
import shutil

# Downloading a tiny 2-second public domain mp3 for demo purposes
TINY_MP3_URL = "https://actions.google.com/sounds/v1/water/rain_on_roof.ogg"

try:
    print("Downloading base audio...")
    urllib.request.urlretrieve(TINY_MP3_URL, "base.ogg")
    
    # We'll just copy it 10 times and pretend they are mp3s (browser `<audio>` can play ogg disguised as mp3 usually, or we just rely on Vite handling it)
    for i in range(1, 11):
        shutil.copy("base.ogg", f"{i}.mp3")
        print(f"Created {i}.mp3")
        
    print("Success")
except Exception as e:
    print(f"Failed: {e}")
