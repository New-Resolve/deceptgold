import subprocess
import sys

def main():
    command = "git-cliff --config utils/config/cliff.toml -o src/deceptgold/CHANGELOG"
    subprocess.run(command, shell=True, check=True)