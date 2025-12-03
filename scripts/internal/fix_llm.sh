#!/bin/bash
echo "=== Fixing LLM Dependencies ==="
echo "1. Installing build tools (cmake)..."
sudo apt update
sudo apt install -y cmake build-essential

echo "2. Installing Python LLM packages..."
# Try installing for system python (likely used by run_agent_system.bat)
pip3 install --upgrade pip setuptools wheel --break-system-packages
pip3 install llama-cpp-python huggingface-hub --break-system-packages

echo "=== Done! LLM support should be fixed. ==="
