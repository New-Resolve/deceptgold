#!/bin/bash

echo "[+] Ativando ambiente virtual do Poetry"
. $(poetry env info --path)/bin/activate

echo "[+] Limpando diretórios anteriores"
rm -rf src_obf/
rm -rf src/deceptgold.dist-info
mkdir -p src_obf

echo "[+] Ofuscando código com PyArmor"
poetry run pyarmor gen -O src_obf -r -i src/deceptgold --platform linux.x86_64

echo "[+] Copiando arquivos necessarios para empacotamento"
cp -r src/deceptgold/resources src_obf/deceptgold/
cp -r src/deceptgold/CHANGELOG src_obf/deceptgold/
cp -r src/deceptgold/LICENSE src_obf/deceptgold/
cp -r src/deceptgold/NOTICE src_obf/deceptgold/

echo "[+] Iniciando build com Briefcase. Actual options: ['fedora:40', 'debian', 'ubuntu']"
poetry run briefcase build --target debian --update

echo "[+] Empacotando aplicação"
poetry run briefcase package --target debian

echo "[+] Limpando temporários"
rm -rf src_obf
rm -rf src/deceptgold.dist-info

echo "================================================================================="
echo "✔️  Use os arquivos no diretório 'dist/' como versões empacotadas para distribuição."
echo "================================================================================="
