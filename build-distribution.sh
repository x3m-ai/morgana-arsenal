#!/bin/bash
#
# Morgana Arsenal Distribution Builder
# Creates/updates the installation package and distribution archive
#
# Usage: ./build-distribution.sh [version]
# Example: ./build-distribution.sh 1.1
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
MORGANA_HOME="/home/morgana/morgana-arsenal"
INSTALL_PKG="${MORGANA_HOME}/install-package"
VERSION="${1:-1.0}"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Archive names
TAR_NAME="morgana-arsenal-complete-v${VERSION}.tar.gz"
ZIP_NAME="morgana-arsenal-install-package-v${VERSION}.zip"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Morgana Arsenal Distribution Builder${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "Version: ${GREEN}${VERSION}${NC}"
echo -e "Date: ${GREEN}${DATE}${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "${MORGANA_HOME}" ]; then
    echo -e "${RED}Error: ${MORGANA_HOME} not found${NC}"
    exit 1
fi

cd "${MORGANA_HOME}"

# ============================================
# Step 1: Update install-package contents
# ============================================
echo -e "${YELLOW}[1/5] Updating install-package contents...${NC}"

# Update HTML files
echo -e "  Copying HTML files..."
cp -f "${MORGANA_HOME}/static/launcher.html" "${INSTALL_PKG}/html/" 2>/dev/null || true
cp -f "${MORGANA_HOME}/static/vm-services-guide.html" "${INSTALL_PKG}/html/" 2>/dev/null || true

# Update VM_COMPLETE_INSTALLATION_GUIDE.md
if [ -f "${MORGANA_HOME}/VM_COMPLETE_INSTALLATION_GUIDE.md" ]; then
    cp -f "${MORGANA_HOME}/VM_COMPLETE_INSTALLATION_GUIDE.md" "${INSTALL_PKG}/"
    echo -e "  ${GREEN}Updated installation guide${NC}"
fi

# Try to update SSL certificates (requires sudo)
if [ -f "/etc/nginx/ssl/caldera.crt" ] && [ -f "/etc/nginx/ssl/caldera.key" ]; then
    if sudo -n true 2>/dev/null; then
        sudo cp /etc/nginx/ssl/caldera.crt "${INSTALL_PKG}/ssl/"
        sudo cp /etc/nginx/ssl/caldera.key "${INSTALL_PKG}/ssl/"
        sudo chown $(whoami):$(whoami) "${INSTALL_PKG}/ssl/"*
        echo -e "  ${GREEN}Updated SSL certificates${NC}"
    else
        echo -e "  ${YELLOW}Skipping SSL update (requires sudo)${NC}"
    fi
fi

# Update nginx configs from system (if accessible)
for conf in caldera-proxy launcher.conf misp.conf misp-https.conf; do
    if [ -f "/etc/nginx/sites-available/${conf}" ]; then
        if sudo -n true 2>/dev/null; then
            sudo cp "/etc/nginx/sites-available/${conf}" "${INSTALL_PKG}/nginx/"
            sudo chown $(whoami):$(whoami) "${INSTALL_PKG}/nginx/${conf}"
        fi
    fi
done

# Update systemd services from system (if accessible)
for svc in morgana-arsenal.service misp-modules.service; do
    if [ -f "/etc/systemd/system/${svc}" ]; then
        if sudo -n true 2>/dev/null; then
            sudo cp "/etc/systemd/system/${svc}" "${INSTALL_PKG}/systemd/"
            sudo chown $(whoami):$(whoami) "${INSTALL_PKG}/systemd/${svc}"
        fi
    fi
done

echo -e "  ${GREEN}Install package updated${NC}"
echo ""

# ============================================
# Step 2: Create ZIP of install-package only
# ============================================
echo -e "${YELLOW}[2/5] Creating install-package ZIP...${NC}"

cd "${MORGANA_HOME}"
rm -f "${ZIP_NAME}" 2>/dev/null || true
zip -r "${ZIP_NAME}" install-package -x "*.pyc" -x "*__pycache__*"

echo -e "  ${GREEN}Created: ${ZIP_NAME}${NC}"
echo ""

# ============================================
# Step 3: Create complete TAR.GZ archive
# ============================================
echo -e "${YELLOW}[3/5] Creating complete distribution archive...${NC}"

cd /home/morgana
rm -f "${TAR_NAME}" 2>/dev/null || true

tar --exclude='morgana-arsenal/venv' \
    --exclude='morgana-arsenal/.git' \
    --exclude='morgana-arsenal/__pycache__' \
    --exclude='morgana-arsenal/*/__pycache__' \
    --exclude='morgana-arsenal/*/*/__pycache__' \
    --exclude='morgana-arsenal/*/*/*/__pycache__' \
    --exclude='morgana-arsenal/*.pyc' \
    --exclude='morgana-arsenal/data/object_store' \
    --exclude='morgana-arsenal/data/fact_store' \
    --exclude='morgana-arsenal/*.log' \
    --exclude='morgana-arsenal/caldera-*.log' \
    --exclude='morgana-arsenal/plugins/magma/node_modules' \
    --exclude='morgana-arsenal/morgana-arsenal-*.tar.gz' \
    --exclude='morgana-arsenal/morgana-arsenal-*.zip' \
    -czf "${TAR_NAME}" morgana-arsenal

echo -e "  ${GREEN}Created: ${TAR_NAME}${NC}"
echo ""

# ============================================
# Step 4: Copy to Desktop
# ============================================
echo -e "${YELLOW}[4/5] Copying archives to Desktop...${NC}"

mkdir -p ~/Desktop
cp "/home/morgana/${TAR_NAME}" ~/Desktop/
cp "${MORGANA_HOME}/${ZIP_NAME}" ~/Desktop/

# Also copy HTML files to desktop
cp "${INSTALL_PKG}/html/launcher.html" ~/Desktop/ 2>/dev/null || true
cp "${INSTALL_PKG}/html/vm-services-guide.html" ~/Desktop/ 2>/dev/null || true

echo -e "  ${GREEN}Files copied to Desktop${NC}"
echo ""

# ============================================
# Step 5: Show summary
# ============================================
echo -e "${YELLOW}[5/5] Distribution Summary${NC}"
echo ""

echo -e "${GREEN}Archives created:${NC}"
ls -lh "/home/morgana/${TAR_NAME}"
ls -lh "${MORGANA_HOME}/${ZIP_NAME}"
echo ""

echo -e "${GREEN}Files on Desktop:${NC}"
ls -lh ~/Desktop/*.tar.gz ~/Desktop/*.zip ~/Desktop/*.html 2>/dev/null || true
echo ""

echo -e "${GREEN}Install package contents:${NC}"
find "${INSTALL_PKG}" -type f | wc -l
echo "files in install-package"
echo ""

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Distribution Build Complete!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "Version: ${GREEN}v${VERSION}${NC}"
echo -e "Complete archive: ${GREEN}${TAR_NAME}${NC} ($(ls -lh /home/morgana/${TAR_NAME} | awk '{print $5}'))"
echo -e "Install package: ${GREEN}${ZIP_NAME}${NC} ($(ls -lh ${MORGANA_HOME}/${ZIP_NAME} | awk '{print $5}'))"
echo ""
echo -e "To install on new VM:"
echo -e "  1. tar -xzvf ${TAR_NAME} -C /home/morgana/"
echo -e "  2. cd /home/morgana/morgana-arsenal"
echo -e "  3. python3 -m venv venv && source venv/bin/activate"
echo -e "  4. pip install -r requirements.txt"
echo -e "  5. sudo ./install-package/scripts/install.sh"
echo ""
