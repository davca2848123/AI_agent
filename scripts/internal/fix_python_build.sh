#!/bin/bash
echo "=== Fixing Python 3.12 Build (Missing SQLite) ==="
echo "1. Installing libsqlite3-dev..."
sudo apt update
sudo apt install -y libsqlite3-dev build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget libbz2-dev liblzma-dev tk-dev

echo "2. Preparing Python source..."
cd /tmp
if [ ! -d "Python-3.12.0" ]; then
    echo "Downloading Python 3.12.0..."
    wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz
    tar -xf Python-3.12.0.tgz
fi

cd Python-3.12.0

echo "3. Configuring..."
./configure --enable-optimizations

echo "4. Compiling (This will take 10-30 minutes)..."
make -j $(nproc)

echo "5. Installing..."
sudo make altinstall

echo "=== Done! SQLite support should be fixed. ==="
