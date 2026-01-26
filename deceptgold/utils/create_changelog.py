import subprocess


def main():
    # git-cliff will use the config file located in the utils directory
    result = subprocess.run("git-cliff --unreleased --config utils/config/cliff.toml", shell=True, check=True, capture_output=True, text=True)
    output = result.stdout
    with open("src/deceptgold/CHANGELOG", "w") as f:
        f.write(output)

if __name__ == "__main__":
    main()