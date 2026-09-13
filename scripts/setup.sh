#!/bin/bash
set -e

echo "======================================"
echo " Hunter Unchained - One-Shot Setup"
echo "======================================"

sudo apt update
sudo apt install -y python3.11 python3-pip python3.11-venv gnupg docker.io tor wget curl

if [ ! -d "venv" ]; then
    python3.11 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -e .

echo ""
echo "Choose model backend:"
echo "1) Ollama"
echo "2) llama.cpp"
echo "3) Auto (recommended)"
read -p "Enter choice [1-3]: " back_choice

case $back_choice in
    1)
        curl -fsSL https://ollama.com/install.sh | sh
        ollama pull hermes2-pro-mistral:7b
        sed -i 's/provider:.*/provider: "ollama"/' hunter_unchained.yaml
        ;;
    2)
        pip install llama-cpp-python
        mkdir -p models
        if [ ! -f models/mistral-7b-instruct-v0.2.Q4_K_M.gguf ]; then
            wget -O models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
                https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
        fi
        sed -i 's/provider:.*/provider: "llama_cpp"/' hunter_unchained.yaml
        ;;
    3|*)
        pip install ollama llama-cpp-python
        if command -v ollama &>/dev/null; then
            ollama pull hermes2-pro-mistral:7b || echo "Ollama pull failed, but that's okay."
        fi
        mkdir -p models
        if [ ! -f models/mistral-7b-instruct-v0.2.Q4_K_M.gguf ]; then
            wget -O models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
                https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
        fi
        sed -i 's/provider:.*/provider: "auto"/' hunter_unchained.yaml
        ;;
esac

sudo systemctl start tor
sudo systemctl enable tor

if [ -f Dockerfile.sandbox ]; then
    docker build -t hunter-sandbox:latest -f Dockerfile.sandbox .
fi

mkdir -p data/knowledge data/sessions data/reports

if ! gpg --list-secret-keys | grep -q "sec"; then
    echo "No GPG key found. Generating one..."
    gpg --batch --gen-key <<EOF
%echo Generating GPG key...
Key-Type: RSA
Key-Length: 4096
Name-Real: Hunter Master
Expire-Date: 0
%no-protection
%commit
%echo Done
EOF
fi
FINGERPRINT=$(gpg --list-keys --with-colons | grep "^fpr" | head -1 | cut -d: -f10)
echo "GPG fingerprint: $FINGERPRINT"
echo "Copy this into hunter_unchained.yaml under master.gpg_key_fingerprint"

echo "[*] Downloading initial CVE data..."
python scripts/cve_ingest.py || echo "CVE ingest skipped."

echo ""
echo "======================================"
echo " SETUP COMPLETE"
echo "======================================"
echo "1. Edit hunter_unchained.yaml with your GPG fingerprint and target scope."
echo "2. Run: source venv/bin/activate && hunter"