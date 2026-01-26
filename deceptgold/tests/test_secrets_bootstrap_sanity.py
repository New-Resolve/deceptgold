from pathlib import Path


def test_secrets_generated_exists_in_checkout():
    repo_root = Path(__file__).resolve().parent.parent
    assert (repo_root / "pyproject.toml").is_file()

    secrets_generated = repo_root / "src" / "deceptgold" / "_secrets_generated.py"
    assert secrets_generated.is_file(), (
        "Missing required secrets file: src/deceptgold/_secrets_generated.py. "
        "Run: poetry run bootstrap-secrets"
    )


def test_secrets_generated_module_imports():
    try:
        from deceptgold import _secrets_generated  # noqa: F401
    except Exception as exc:
        raise AssertionError(
            "Failed to import deceptgold._secrets_generated. Run: poetry run bootstrap-secrets"
        ) from exc
