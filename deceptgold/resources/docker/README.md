# Dockerfile

## Use this file if you want to use it in a practical way using docker.

###  Just uncomment which operating system you want to use.

Save the file below as `Dockerfile`
```
FROM ubuntu:noble
# FROM debian:bookworm
# FROM fedora:42

RUN set -e && \
    DISTRO=$(grep "^ID=" /etc/os-release | cut -d= -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]') && \
    echo "🔍 Installing dependencies for distribution: $DISTRO" && \
    case "$DISTRO" in \
      debian|ubuntu) \
        apt-get update && \
        apt-get install -y wget curl ca-certificates jq gnupg lsb-release git vim nano make && \
        apt-get clean; \
        ;; \
      fedora) \
        dnf -y update && \
        dnf install -y wget curl ca-certificates jq redhat-lsb-core git vim nano make && \
        dnf clean all; \
        ;; \
      *) \
        echo "❌ Unsupported distribution for package installation: $DISTRO"; \
        exit 1; \
        ;; \
    esac

RUN set -e && \
    DISTRO=$(grep "^ID=" /etc/os-release | cut -d= -f2 | tr -d '"' | tr '[:upper:]' '[:lower:]') && \
    echo "🔍 Detecting distribution for deceptgold installation: $DISTRO" && \
    case "$DISTRO" in \
      debian) \
        ASSET=$(curl -s https://api.github.com/repos/New-Resolve/deceptgold/releases/latest | \
                jq -r '.assets[] | select(.name | endswith("debian-bookworm_amd64.deb")) | .browser_download_url'); \
        PACKAGE="deceptgold.deb"; \
        wget "$ASSET" -O "$PACKAGE"; \
        apt-get update && apt-get install -y ./"$PACKAGE"; \
        ;; \
      ubuntu) \
        ASSET=$(curl -s https://api.github.com/repos/New-Resolve/deceptgold/releases/latest | \
                jq -r '.assets[] | select(.name | endswith("ubuntu-noble_amd64.deb")) | .browser_download_url'); \
        PACKAGE="deceptgold.deb"; \
        wget "$ASSET" -O "$PACKAGE"; \
        apt-get update && apt-get install -y ./"$PACKAGE"; \
        ;; \
      fedora) \
        ASSET=$(curl -s https://api.github.com/repos/New-Resolve/deceptgold/releases/latest | \
                jq -r '.assets[] | select(.name | endswith(".x86_64.rpm")) | .browser_download_url'); \
        PACKAGE="deceptgold.rpm"; \
        wget "$ASSET" -O "$PACKAGE"; \
        dnf install -y ./"$PACKAGE"; \
        ;; \
      *) \
        echo "❌ Unsupported distribution for deceptgold: $DISTRO"; \
        exit 1; \
        ;; \
    esac && rm -f "$PACKAGE"


EXPOSE 2121 2222 8090

# Default command to start deceptgold in development mode
# Developers can override with `docker run -it <image> bash` for interactive debugging
# CMD ["deceptgold", "service", "start", "daemon=false", "force-no-wallet=true"]
CMD ["deceptgold", "--help"]
```

Build the file with the command: `docker build -t deceptgold .`

Congratulations, now you can use deceptgold easily.

