#!/bin/bash

echo "Building C# agent with Mono..."

# Check if mono is installed
if ! command -v mcs &> /dev/null; then
    echo "Installing mono..."
    sudo apt update
    sudo apt install -y mono-mcs mono-runtime
fi

cd /home/morgana/caldera/agent-sharp

# Compile for .NET 4.x (compatible with Windows)
mcs -out:MerlinoSharp.exe -target:winexe -platform:x64 -optimize+ Agent.cs

if [ -f MerlinoSharp.exe ]; then
    mv MerlinoSharp.exe /home/morgana/caldera/data/payloads/
    echo "Success! Binary at: data/payloads/MerlinoSharp.exe"
    ls -lh /home/morgana/caldera/data/payloads/MerlinoSharp.exe
else
    echo "Compilation failed"
    exit 1
fi
