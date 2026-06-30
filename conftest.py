import sys
import os

# Das App-Paket liegt im Repo-Root; pytest muss vom Elternverzeichnis importieren.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
