import argparse
import json
import os
import subprocess
from pathlib import Path


DEFAULT_SECRETS_FILENAME = "secrets.enc.json"
DEFAULT_SECRETS_REPO_DIR = Path.home() / ".cache" / "deceptgold" / "secrets-repo"
DEFAULT_SECRETS_REPO_BRANCH = "main"


def _run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout
    except FileNotFoundError as e:
        tool = cmd[0]
        raise RuntimeError(
            f"Command not found: {tool}. This is a system dependency (not a Python package).\n"
            f"Install hints:\n"
            f"- Ubuntu/Debian: sudo apt install {tool}\n"
            f"- Fedora: sudo dnf install {tool}\n"
            f"- macOS: brew install {tool}\n"
            f"- Windows: winget install Mozilla.SOPS (for sops) / winget install FiloSottile.age (for age)\n"
        ) from e
    except subprocess.CalledProcessError as e:
        msg = e.stderr.strip() or e.stdout.strip() or str(e)
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{msg}") from e


def _decrypt_with_sops(enc_file: Path) -> dict:
    # Ensure sops and age exist early with clear errors.
    _run(["sops", "--version"])
    _run(["age", "--version"])
    stdout = _run(["sops", "-d", str(enc_file)])
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Decrypted secrets is not valid JSON. "
            "Recommended format is a JSON object (key/value) encrypted with sops."
        ) from e


def _git_clone_or_update(repo_url: str, repo_dir: Path, branch: str) -> None:
    # Ensure git exists early with clear errors.
    _run(["git", "--version"])

    repo_dir = repo_dir.expanduser().resolve()
    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    if not repo_dir.exists():
        _run([
            "git",
            "clone",
            "--branch",
            branch,
            "--single-branch",
            repo_url,
            str(repo_dir),
        ])
        return

    git_dir = repo_dir / ".git"
    if not git_dir.exists():
        raise RuntimeError(
            f"Secrets repo dir exists but is not a git repository: {repo_dir}\n"
            f"Either remove it, or pass a different --secrets-repo-dir."
        )

    # Safe update by default: fast-forward only.
    _run(["git", "-C", str(repo_dir), "fetch", "origin", branch])
    _run(["git", "-C", str(repo_dir), "checkout", branch])
    _run(["git", "-C", str(repo_dir), "pull", "--ff-only", "origin", branch])


def _infer_secrets_repo_url_from_origin(project_dir: Path) -> str:
    """Infer the secrets repo URL from the current repo origin.

    Assumption: secrets repo lives under the same owner/org and host, with name:

    - deceptgold -> deceptgold-secrets
    """

    # Ensure git exists early with clear errors.
    _run(["git", "--version"])

    git_root = _run(["git", "-C", str(project_dir), "rev-parse", "--show-toplevel"]).strip()
    origin = _run(["git", "-C", git_root, "remote", "get-url", "origin"]).strip()

    # Normalize common patterns:
    # - git@github.com:ORG/deceptgold.git
    # - https://github.com/ORG/deceptgold.git
    # - https://github.com/ORG/deceptgold
    if origin.endswith("/deceptgold"):
        return origin[:-len("/deceptgold")] + "/deceptgold-secrets"
    if origin.endswith("/deceptgold.git"):
        return origin[:-len("/deceptgold.git")] + "/deceptgold-secrets.git"
    if origin.endswith(":deceptgold"):
        return origin[:-len(":deceptgold")] + ":deceptgold-secrets"
    if origin.endswith(":deceptgold.git"):
        return origin[:-len(":deceptgold.git")] + ":deceptgold-secrets.git"

    raise RuntimeError(
        "Unable to infer secrets repo URL from git origin. "
        f"Expected origin to end with 'deceptgold' (or 'deceptgold.git'), got: {origin}\n"
        "Provide --secrets-repo-url or set DECEPTGOLD_SECRETS_REPO_URL explicitly."
    )


def _render_python_module(secrets: dict) -> str:
    # Keep it deterministic and simple; values must be strings.
    normalized: dict[str, str] = {}
    for k, v in secrets.items():
        if v is None:
            normalized[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            normalized[k] = str(v)
        else:
            raise RuntimeError(f"Unsupported value type for key '{k}': {type(v)}")

    return "SECRETS = " + json.dumps(normalized, indent=4, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deceptgold _secrets_generated.py from a SOPS-encrypted secrets file")
    parser.add_argument(
        "--secrets-file",
        default=os.environ.get("DECEPTGOLD_SECRETS_FILE", ""),
        help="Path to SOPS-encrypted JSON file (default: env DECEPTGOLD_SECRETS_FILE)",
    )
    parser.add_argument(
        "--secrets-repo",
        default=os.environ.get("DECEPTGOLD_SECRETS_REPO", ""),
        help="Path to local secrets repo folder (default: env DECEPTGOLD_SECRETS_REPO). If provided, secrets-file defaults to <repo>/secrets.enc.json",
    )
    parser.add_argument(
        "--secrets-repo-url",
        default=os.environ.get("DECEPTGOLD_SECRETS_REPO_URL", ""),
        help="Git URL of the private secrets repo. If provided, the repo will be cloned/updated automatically.",
    )
    parser.add_argument(
        "--secrets-repo-dir",
        default=os.environ.get("DECEPTGOLD_SECRETS_REPO_DIR", str(DEFAULT_SECRETS_REPO_DIR)),
        help="Local directory for the secrets repo when using --secrets-repo-url (default: ~/.cache/deceptgold/secrets-repo)",
    )
    parser.add_argument(
        "--secrets-repo-branch",
        default=os.environ.get("DECEPTGOLD_SECRETS_REPO_BRANCH", DEFAULT_SECRETS_REPO_BRANCH),
        help="Branch to clone/pull when using --secrets-repo-url (default: main)",
    )

    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parents[1]

    # Zero-config mode: if no secrets source is provided, infer the secrets repo URL
    # from the current deceptgold git origin.
    if not args.secrets_file and not args.secrets_repo and not args.secrets_repo_url:
        args.secrets_repo_url = _infer_secrets_repo_url_from_origin(project_root)

    # Optional automation: clone/update secrets repo from git.
    # If provided, this takes precedence over --secrets-repo.
    if args.secrets_repo_url:
        repo_dir = Path(args.secrets_repo_dir)
        _git_clone_or_update(args.secrets_repo_url, repo_dir, args.secrets_repo_branch)
        args.secrets_repo = str(repo_dir)

    secrets_file = args.secrets_file
    if not secrets_file and args.secrets_repo:
        secrets_file = str(Path(args.secrets_repo) / DEFAULT_SECRETS_FILENAME)

    if not secrets_file:
        raise RuntimeError(
            "Missing secrets source. Provide --secrets-file, or set DECEPTGOLD_SECRETS_FILE, "
            "or provide --secrets-repo / DECEPTGOLD_SECRETS_REPO."
        )

    enc_file = Path(secrets_file).expanduser().resolve()
    if not enc_file.exists():
        raise RuntimeError(f"Secrets file does not exist: {enc_file}")

    secrets = _decrypt_with_sops(enc_file)

    target = project_root / "src" / "deceptgold" / "_secrets_generated.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_render_python_module(secrets), encoding="utf-8")

    print(f"Generated: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
