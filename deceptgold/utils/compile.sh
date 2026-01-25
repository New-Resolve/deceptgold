#!/bin/bash

set -e

MODE="${1:---all}"
if [ "$MODE" != "--deb" ] && [ "$MODE" != "--rpm" ] && [ "$MODE" != "--all" ]; then
  echo "Usage: $0 [--deb|--rpm|--all]"
  exit 2
fi

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

echo "[+] Gerando pacote(s) standalone com Python embutido (mantém comando 'deceptgold')"

VERSION=$(poetry version -s)
ARCH=$(dpkg --print-architecture)
PKGDIR=$(mktemp -d)

PYTHON_BASE_PREFIX=$(python -c 'import sys; print(sys.base_prefix)')
PYTHON_SITE_PACKAGES=$(python -c 'import site; print(site.getsitepackages()[0])')

mkdir -p dist

mkdir -p "$PKGDIR/DEBIAN"
mkdir -p "$PKGDIR/usr/bin"
mkdir -p "$PKGDIR/usr/lib/deceptgold/app"
mkdir -p "$PKGDIR/usr/lib/deceptgold/python"
mkdir -p "$PKGDIR/usr/lib/deceptgold/app_packages"

echo "[+] Copiando código ofuscado para /usr/lib/deceptgold/app"
cp -a src_obf/deceptgold "$PKGDIR/usr/lib/deceptgold/app/"

echo "[+] Embutindo runtime do Python (base_prefix: $PYTHON_BASE_PREFIX)"
cp -a "$PYTHON_BASE_PREFIX"/* "$PKGDIR/usr/lib/deceptgold/python/"

echo "[+] Copiando dependências Python do venv (site-packages: $PYTHON_SITE_PACKAGES)"
cp -a "$PYTHON_SITE_PACKAGES"/* "$PKGDIR/usr/lib/deceptgold/app_packages/" || true

cat > "$PKGDIR/usr/bin/deceptgold" <<'EOF'
#!/bin/sh
APP_ROOT="/usr/lib/deceptgold"
export PYTHONHOME="$APP_ROOT/python"
export PYTHONPATH="$APP_ROOT/app:$APP_ROOT/app_packages"
exec "$APP_ROOT/python/bin/python3" -m deceptgold "$@"
EOF
chmod 0755 "$PKGDIR/usr/bin/deceptgold"

build_deb() {
  mkdir -p "$PKGDIR/DEBIAN"
  cat > "$PKGDIR/DEBIAN/control" <<EOF
Package: deceptgold
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Maintainer: Jonathan Scheibel <jonathan@deceptgold.com>
Description: Deceptgold
EOF

  DEB_OUT="dist/deceptgold_${VERSION}-1~standalone_${ARCH}.deb"
  dpkg-deb --root-owner-group --build "$PKGDIR" "$DEB_OUT"
  echo "[+] Standalone DEB gerado: $DEB_OUT"
}

build_rpm() {
  if ! command -v rpmbuild >/dev/null 2>&1; then
    echo "[!] rpmbuild não encontrado. Instale rpmbuild/rpm-build antes de gerar .rpm."
    exit 1
  fi

  RPMTOP=$(mktemp -d)
  mkdir -p "$RPMTOP"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

  PAYLOAD_DIR=$(mktemp -d)
  cp -a "$PKGDIR"/* "$PAYLOAD_DIR"/
  rm -rf "$PAYLOAD_DIR/DEBIAN" || true

  TAR_NAME="deceptgold-${VERSION}.tar.gz"
  tar -C "$PAYLOAD_DIR" -czf "$RPMTOP/SOURCES/$TAR_NAME" .

  SPEC_FILE="$RPMTOP/SPECS/deceptgold.spec"
  cat > "$SPEC_FILE" <<EOF
Name: deceptgold
Version: ${VERSION}
Release: 1%{?dist}
Summary: Deceptgold
License: Proprietary
BuildArch: x86_64
Source0: ${TAR_NAME}

%description
Deceptgold

%prep
%setup -q

%build

%install
mkdir -p %{buildroot}
cp -a * %{buildroot}/

%files
/usr/bin/deceptgold
/usr/lib/deceptgold

%changelog
EOF

  rpmbuild --define "_topdir $RPMTOP" -bb "$SPEC_FILE"
  RPM_OUT=$(find "$RPMTOP/RPMS" -type f -name '*.rpm' | head -n 1)
  if [ -z "$RPM_OUT" ]; then
    echo "[!] Falha ao gerar RPM."
    exit 1
  fi
  cp "$RPM_OUT" "dist/$(basename "$RPM_OUT" | sed 's/^deceptgold-/deceptgold_/')"
  echo "[+] Standalone RPM gerado: dist/$(basename "$RPM_OUT" | sed 's/^deceptgold-/deceptgold_/')"

  rm -rf "$RPMTOP" "$PAYLOAD_DIR"
}

if [ "$MODE" = "--deb" ] || [ "$MODE" = "--all" ]; then
  build_deb
fi

if [ "$MODE" = "--rpm" ] || [ "$MODE" = "--all" ]; then
  build_rpm
fi

rm -rf "$PKGDIR"

echo "[+] Limpando temporários"
rm -rf src_obf
rm -rf src/deceptgold.dist-info

echo "================================================================================="
echo "✔️  Use os arquivos no diretório 'dist/' como versões empacotadas para distribuição."
echo "================================================================================="
