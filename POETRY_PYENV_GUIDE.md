# Guia Rápido: Poetry 2.0 + pyenv

## Problema Comum

```
Current Python version (3.10.x) is not allowed by the project (^3.11).
```

## Solução Rápida

### 1. Instalar Python 3.12 com pyenv

```bash
# Instalar pyenv (se não tiver)
curl https://pyenv.run | bash

# Adicionar ao ~/.bashrc ou ~/.zshrc
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Recarregar shell
source ~/.bashrc

# Instalar Python 3.12
pyenv install 3.12

# Definir como versão local do projeto
cd deceptgold/deceptgold
pyenv local 3.12

# Verificar
python --version  # Deve mostrar Python 3.12.x
```

### 2. Configurar Poetry

```bash
# Habilitar criação de virtualenv
poetry config virtualenvs.create true

# Dizer ao Poetry para usar o Python correto
poetry env use python

# Instalar dependências
poetry install
```

### 3. Ativar Ambiente (Poetry 2.0+)

**Opção 1: Ativação Manual (Recomendado)**
```bash
source .venv/bin/activate
python -m deceptgold --version
```

**Opção 2: Usar `poetry run`**
```bash
poetry run python -m deceptgold --version
poetry run briefcase dev --
poetry run pytest
```

**Opção 3: Instalar Plugin Shell**
```bash
poetry self add poetry-plugin-shell
poetry shell
```

## Comandos Úteis

```bash
# Ver informações do ambiente Poetry
poetry env info

# Ver qual Python o Poetry está usando
poetry env info --path

# Remover ambiente e recriar
poetry env remove python
poetry env use python
poetry install

# Listar ambientes
poetry env list

# Verificar configuração do Poetry
poetry config --list
```

## Troubleshooting

### Poetry não encontra Python correto

```bash
# Especificar caminho completo
poetry env use $(which python)

# Ou especificar versão
poetry env use 3.12
```

### Ambiente virtual não é criado

```bash
# Verificar configuração
poetry config virtualenvs.create

# Deve retornar: true
# Se retornar false, execute:
poetry config virtualenvs.create true
```

### `poetry shell` não funciona

```bash
# Poetry 2.0+ não tem shell por padrão
# Use uma das 3 opções acima
```

## Referências

- [DEVELOPMENT.md](../DEVELOPMENT.md) - Guia completo de desenvolvimento
- [GETTING_STARTED.md](deceptgold/docs/GETTING_STARTED.md) - Início rápido
- [Poetry Docs](https://python-poetry.org/docs/managing-environments/)
- [pyenv Docs](https://github.com/pyenv/pyenv)
