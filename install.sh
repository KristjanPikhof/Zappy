#!/bin/bash
#
# Zappy the VPS Toolbox Installer
# Detects Linux distribution and installs dependencies
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Installation paths
INSTALL_DIR="/opt/zappy"
VENV_DIR="$INSTALL_DIR/venv"
BIN_LINK="/usr/local/bin/zappy"
REPO_URL="https://github.com/KristjanPikhof/Zappy.git"
TEMP_CLONE_DIR="/tmp/zappy-install"

# Print functions
print_header() {
    echo -e "\n${BLUE}===================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}===================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        DISTRO_ID="$ID"
        DISTRO_NAME="$NAME"
        DISTRO_VERSION="$VERSION_ID"
        DISTRO_ID_LIKE="$ID_LIKE"
    else
        print_error "Cannot detect distribution. /etc/os-release not found."
        exit 1
    fi

    print_info "Detected: $DISTRO_NAME ($DISTRO_ID)"
}

# Detect package manager
detect_package_manager() {
    if command -v apt &> /dev/null; then
        PKG_MANAGER="apt"
        PKG_UPDATE="apt update"
        PKG_INSTALL="apt install -y"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        PKG_UPDATE="dnf check-update || true"
        PKG_INSTALL="dnf install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        PKG_UPDATE="yum check-update || true"
        PKG_INSTALL="yum install -y"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        PKG_UPDATE="pacman -Sy"
        PKG_INSTALL="pacman -S --noconfirm"
    elif command -v apk &> /dev/null; then
        PKG_MANAGER="apk"
        PKG_UPDATE="apk update"
        PKG_INSTALL="apk add"
    elif command -v zypper &> /dev/null; then
        PKG_MANAGER="zypper"
        PKG_UPDATE="zypper refresh"
        PKG_INSTALL="zypper install -y"
    else
        print_error "No supported package manager found."
        exit 1
    fi

    print_info "Package manager: $PKG_MANAGER"
}

# Get package names for current distro
get_packages() {
    # Base packages needed
    case "$PKG_MANAGER" in
        apt)
            PACKAGES="python3 python3-pip python3-venv nginx certbot python3-certbot-nginx curl wget git"
            ;;
        dnf|yum)
            PACKAGES="python3 python3-pip nginx certbot python3-certbot-nginx curl wget git"
            ;;
        pacman)
            PACKAGES="python python-pip nginx certbot certbot-nginx curl wget git"
            ;;
        apk)
            PACKAGES="python3 py3-pip nginx certbot certbot-nginx curl wget git"
            ;;
        zypper)
            PACKAGES="python3 python3-pip nginx certbot python3-certbot-nginx curl wget git"
            ;;
    esac
}

# Ensure repo is available (clone if running standalone)
ensure_repo() {
    if [ -d "zappy" ] && [ -f "setup.py" ]; then
        # Already in repo directory
        print_info "Running from cloned repository."
        WORK_DIR="$(pwd)"
    else
        # Need to clone the repo
        print_info "Cloning Zappy repository..."

        # Check if git is available
        if ! command -v git &> /dev/null; then
            print_error "Git is not installed. Installing git first..."
            # Try to install git based on available package manager
            if command -v apt &> /dev/null; then
                apt update && apt install -y git
            elif command -v dnf &> /dev/null; then
                dnf install -y git
            elif command -v yum &> /dev/null; then
                yum install -y git
            elif command -v pacman &> /dev/null; then
                pacman -Sy --noconfirm git
            elif command -v apk &> /dev/null; then
                apk add git
            elif command -v zypper &> /dev/null; then
                zypper install -y git
            else
                print_error "Cannot install git. Please install git manually and try again."
                exit 1
            fi
        fi

        # Remove old temp dir if exists
        rm -rf "$TEMP_CLONE_DIR"

        # Clone the repository
        git clone "$REPO_URL" "$TEMP_CLONE_DIR"

        if [ $? -ne 0 ]; then
            print_error "Failed to clone repository."
            exit 1
        fi

        WORK_DIR="$TEMP_CLONE_DIR"
        cd "$WORK_DIR"
        print_success "Repository cloned to $TEMP_CLONE_DIR"
    fi
}

# Install system dependencies
install_dependencies() {
    print_header "Installing Dependencies"

    print_info "Updating package list..."
    sudo $PKG_UPDATE

    print_info "Installing packages..."
    sudo $PKG_INSTALL $PACKAGES

    print_success "Dependencies installed."
}

# Install Zappy the VPS Toolbox
install_zappy() {
    print_header "Installing Zappy the VPS Toolbox"

    # Create installation directory
    print_info "Creating installation directory..."
    sudo mkdir -p "$INSTALL_DIR"

    # Copy files
    if [ -d "zappy" ]; then
        print_info "Copying Zappy files..."
        sudo cp -r zappy "$INSTALL_DIR/"
        sudo cp setup.py "$INSTALL_DIR/"
        sudo cp requirements.txt "$INSTALL_DIR/"
        sudo cp README.md "$INSTALL_DIR/" 2>/dev/null || true
    else
        print_error "zappy directory not found. Please run from the project root."
        exit 1
    fi

    # Create virtual environment
    print_info "Creating Python virtual environment..."
    sudo python3 -m venv "$VENV_DIR"

    # Install Python dependencies
    print_info "Installing Python dependencies..."
    sudo "$VENV_DIR/bin/pip" install --upgrade pip
    sudo "$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
    sudo "$VENV_DIR/bin/pip" install -e "$INSTALL_DIR"

    # Create symlink
    print_info "Creating global command..."
    sudo ln -sf "$VENV_DIR/bin/zappy" "$BIN_LINK"

    # Set permissions
    sudo chmod +x "$BIN_LINK"

    print_success "Zappy the VPS Toolbox installed!"
}

# Create wrapper script (alternative method)
create_wrapper() {
    print_info "Creating wrapper script..."

    cat << 'EOF' | sudo tee "$BIN_LINK" > /dev/null
#!/bin/bash
INSTALL_DIR="/opt/zappy"
VENV_DIR="$INSTALL_DIR/venv"
source "$VENV_DIR/bin/activate"
python -m zappy "$@"
EOF

    sudo chmod +x "$BIN_LINK"
}

# Uninstall function
uninstall() {
    print_header "Uninstalling Zappy the VPS Toolbox"

    print_info "Removing installation directory..."
    sudo rm -rf "$INSTALL_DIR"

    print_info "Removing symlink..."
    sudo rm -f "$BIN_LINK"

    print_success "Zappy the VPS Toolbox uninstalled."
}

# Main
main() {
    print_header "Zappy the VPS Toolbox Installer"

    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        print_error "This script requires root privileges."
        print_info "Please run with: sudo ./install.sh"
        exit 1
    fi

    # Check for uninstall flag
    if [ "$1" = "--uninstall" ] || [ "$1" = "-u" ]; then
        uninstall
        exit 0
    fi

    # Ensure we have the repo files
    ensure_repo

    # Detect system
    detect_distro
    detect_package_manager
    get_packages

    # Confirm installation
    echo ""
    print_info "This will install Zappy the VPS Toolbox to $INSTALL_DIR"
    print_info "A global command 'zappy' will be created."
    echo ""

    # Skip confirmation if running non-interactively (e.g., piped from curl)
    if [ -t 0 ]; then
        read -p "Continue with installation? [Y/n] " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]] && [[ ! -z $REPLY ]]; then
            print_info "Installation cancelled."
            exit 0
        fi
    else
        print_info "Running non-interactively, proceeding with installation..."
    fi

    # Install
    install_dependencies
    install_zappy

    print_header "Installation Complete!"
    echo ""
    print_success "Zappy the VPS Toolbox has been installed successfully!"
    echo ""
    print_info "Run 'zappy' to start using the tool."
    echo ""

    # Cleanup temp clone if used
    if [ -d "$TEMP_CLONE_DIR" ]; then
        rm -rf "$TEMP_CLONE_DIR"
    fi
}

main "$@"
