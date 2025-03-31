# Instalação e geração distribuição do sistema:

- `cd deceptgold`
- `poetry config virtualenvs.in-project true`
- `export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring`
- `poetry shell`
- `poetry install`
- `sh utils/compile.sh`