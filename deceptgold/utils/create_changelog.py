import subprocess
import sys

def main():
    command = "git-cliff > src/deceptgold/CHANGELOG"
    subprocess.run(command, shell=True, check=True)