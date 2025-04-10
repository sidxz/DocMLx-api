#!/usr/bin/env bash

echo "Installing platform-specific dependencies..."

ARCH=$(uname -m)

if [[ "$ARCH" == "arm64" ]]; then
    echo "Detected Apple Silicon (arm64). Installing spacy[apple]..."
    pipenv run pip install "spacy[apple]"
else
    echo "Detected x86_64 architecture. No additional extras needed."
fi
