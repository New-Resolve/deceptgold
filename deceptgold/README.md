# Installation and configuration ambient development:

- `cd deceptgold`
- `poetry config virtualenvs.in-project true`
- `export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring`
- `poetry shell`
- `poetry install`
- `sh utils/compile.sh`

or run `sh utils/compile.sh` in bash linux environment
