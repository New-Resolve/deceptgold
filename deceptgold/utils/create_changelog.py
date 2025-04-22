import subprocess


def main():
    result = subprocess.run("git-cliff", shell=True, check=True, capture_output=True, text=True)
    output = result.stdout.replace("unreleased", "Last Version")
    with open("src/deceptgold/CHANGELOG", "w") as f:
        f.write(output)

if __name__ == "__main__":
    main()