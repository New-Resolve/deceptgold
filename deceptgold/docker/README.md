# Dockerfile

## Use this file if you want to use it in a practical way using docker.

###  Just uncomment which operating system you want to use.

Save the file below as `Dockerfile`
```
FROM debian:bookworm
# FROM ubuntu:noble
# FROM fedora:40


RUN apt-get update || dnf -y update || true && \
    (apt-get install -y wget curl ca-certificates jq gnupg lsb-release || \
     dnf install -y wget curl ca-certificates jq redhat-lsb-core)


RUN set -e && \
    DISTRO=$( (lsb_release -is 2>/dev/null || grep "^ID=" /etc/os-release | cut -d= -f2) | tr '[:upper:]' '[:lower:]' ) && \
    echo "🔍 Detecting distribution: $DISTRO" && \
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
                jq -r '.assets[] | select(.name | endswith("fc40.x86_64.rpm")) | .browser_download_url'); \
        PACKAGE="deceptgold.rpm"; \
        wget "$ASSET" -O "$PACKAGE"; \
        dnf install -y ./"$PACKAGE"; \
        ;; \
      *) \
        echo "❌ Unsupported distribution: $DISTRO"; \
        exit 1; \
        ;; \
    esac && rm -f "$PACKAGE"


EXPOSE 2121 2222 8090


CMD ["deceptgold", "service", "start", "daemon=false", "force-no-wallet=true"]
```

Build the file with the command: `docker build -t deceptgold .`

Congratulations, now you can use deceptgold easily.

You can use the honeypot in a simple way. Example:
`docker run -it -p 2121:2121 -p 2222:2222 -p 8090:8090 deceptgold`

