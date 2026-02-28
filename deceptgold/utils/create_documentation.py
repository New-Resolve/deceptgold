import argparse
import subprocess
import sys

def main():
    """Generate and optionally serve MkDocs documentation for the Deceptgold project."""
    parser = argparse.ArgumentParser(description="Generate and serve Deceptgold documentation.")
    parser.add_argument("--build-only", action="store_true", help="Only build the documentation, do not serve.")
    args = parser.parse_args()

    build_result = call_build()
    if build_result != 0:
        return build_result

    if not args.build_only:
        return call_serve()

    return 0

def call_serve():
    """Serve MkDocs documentation for the Deceptgold project locally."""
    try:
        result = subprocess.run(
            ["mkdocs", "serve", "-f", "../docs/mkdocs.yml"],
            check=True,
            text=True
        )
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error running mkdocs serve: {e.stderr}", file=sys.stderr)
        return e.returncode
    except FileNotFoundError:
        print("Error: mkdocs not found. Ensure it is installed with 'poetry add mkdocs --group docs'.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nStopped mkdocs serve.", file=sys.stderr)
        return 0

def call_build():
    """Build MkDocs documentation for the Deceptgold project."""
    try:
        result = subprocess.run(
            ["mkdocs", "build", "-f", "../docs/mkdocs.yml"],
            check=True,
            text=True,
            capture_output=True
        )
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(e.stderr, file=sys.stderr)
        return e.returncode
    except FileNotFoundError:
        print("Error: mkdocs not found. Ensure it is installed with 'poetry add mkdocs --group docs'.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())