#!/bin/bash
# Setup Nginx reverse proxy for OpenAgents
# Run on server: bash setup_nginx.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Setting up Nginx for agents.uamgo.com${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Nginx not found, installing...${NC}"
    apt-get update
    apt-get install -y nginx
    echo -e "${GREEN}✓ Nginx installed${NC}"
else
    echo -e "${GREEN}✓ Nginx is already installed${NC}"
fi

# Backup existing config if it exists
CONF_FILE="/etc/nginx/sites-available/agents.uamgo.com.conf"
if [ -f "$CONF_FILE" ]; then
    echo -e "${YELLOW}Backing up existing config...${NC}"
    cp "$CONF_FILE" "$CONF_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✓ Backup created${NC}"
fi

# Copy config file
echo -e "${BLUE}Installing Nginx configuration...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/agents.uamgo.com.conf" "$CONF_FILE"
echo -e "${GREEN}✓ Config file installed${NC}"

# Create symbolic link to sites-enabled
ENABLED_LINK="/etc/nginx/sites-enabled/agents.uamgo.com.conf"
if [ -L "$ENABLED_LINK" ]; then
    rm "$ENABLED_LINK"
fi
ln -s "$CONF_FILE" "$ENABLED_LINK"
echo -e "${GREEN}✓ Config enabled${NC}"

# Test Nginx configuration
echo -e "${BLUE}Testing Nginx configuration...${NC}"
if nginx -t; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}✗ Nginx configuration is invalid${NC}"
    exit 1
fi

# Reload Nginx
echo -e "${BLUE}Reloading Nginx...${NC}"
systemctl reload nginx
echo -e "${GREEN}✓ Nginx reloaded${NC}"

# Check Nginx status
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx is running${NC}"
else
    echo -e "${YELLOW}Starting Nginx...${NC}"
    systemctl start nginx
    echo -e "${GREEN}✓ Nginx started${NC}"
fi

# Enable Nginx to start on boot
systemctl enable nginx
echo -e "${GREEN}✓ Nginx enabled on boot${NC}"

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✓ Nginx setup complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}Access your application:${NC}"
echo -e "  • Studio: ${GREEN}http://agents.uamgo.com/studio/${NC}"
echo -e "  • API: ${GREEN}http://agents.uamgo.com/api/health${NC}"
echo -e "  • MCP: ${GREEN}http://agents.uamgo.com/mcp${NC}"
echo ""
echo -e "${YELLOW}Test the proxy:${NC}"
echo -e "  curl http://agents.uamgo.com/api/health"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo -e "  tail -f /var/log/nginx/agents.uamgo.com.access.log"
echo -e "  tail -f /var/log/nginx/agents.uamgo.com.error.log"
echo ""

