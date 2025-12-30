#!/bin/bash

BASE_DIR=$(cd "$(dirname "$0")" && pwd)

DUMP1090_DIR="$BASE_DIR/opt/dump1090"
DUMP1090_TMP="$BASE_DIR/tmp"
DUMP1090_ZIP="$DUMP1090_TMP/dump1090_source.zip"
DUMP1090_URL="https://github.com/flightaware/dump1090/archive/refs/heads/master.zip"

echo "###########################################"
echo "###                                     ###"
echo "###         MOAE'S FLIGHT TRACKER       ###"
echo "###                                     ###"
echo "###########################################"

mkdir -p "$DUMP1090_TMP"
mkdir -p "$BASE_DIR/opt"

sudo apt update && sudo apt install -y build-essential pkg-config librtlsdr-dev libusb-1.0-0-dev \
    libncurses-dev unzip wget python3-venv python3-pip

echo "Preparing dump1090"
if [ ! -d "$DUMP1090_DIR" ]; then
    echo "Downloading source code..."
    wget -q "$DUMP1090_URL" -O "$DUMP1090_ZIP"
    
    echo "Extracting..."
    unzip -o "$DUMP1090_ZIP" -d "$BASE_DIR"
    
    cp -r "$BASE_DIR/dump1090-master" "$DUMP1090_DIR"
    rm -rf "$BASE_DIR/dump1090-master"
    rm "$DUMP1090_ZIP"
else
    echo "Folder 'dump1090' already exists. Skipping download."
fi

echo "Compiling dump1090..."
cd "$DUMP1090_DIR"
make

"$DUMP1090_DIR/dump1090" --net --quiet &
echo "dump1090 started in background!"

cd "$BASE_DIR"

echo "Preparing Python virtual environment"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
fi

source venv/bin/activate
echo "Installing python dependencies..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

echo "Python environment set up successfully!"
rm -rf "$BASE_DIR/tmp"

python3 App.py