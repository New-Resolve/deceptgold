# Installation and configuration ambient development:

- `cd deceptgold`
- `poetry config virtualenvs.in-project true`
- `export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring`
- `poetry shell`
- `poetry install`
- `sh utils/compile.sh`



###  TODO:
```
( ) - Encontrar problema dos imports (Deixar funcionando tanto por CLI quanto por debug da IDE)
( ) - criar automatização para buildar o codigo já ofuscado com o pyarmor (Atualmente precisa mudar o pyproject + compile.sh)
( ) - Fazer o dist para todas as ditribuições no github (action)
( ) - Criar um arquivo para apagar arquivos desnecessarios
```
