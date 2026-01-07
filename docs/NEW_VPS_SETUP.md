# New VPS Setup Guide

A step-by-step guide to securely set up a brand new VPS from scratch.

> **Warning**: Keep your root SSH session open until you've verified the new user can login and use sudo!

---

## Quick Reference

| Step | Command | Description |
|------|---------|-------------|
| 1 | `adduser USERNAME` | Create new user |
| 2 | `usermod -aG sudo USERNAME` | Grant sudo access |
| 3 | Set up SSH key | Enable key-based login |
| 4 | Test new user login | **Before closing root session!** |
| 5 | `./install.sh` | Install Zappy the VPS Toolbox |
| 6 | `vps-toolbox` | Harden server |

---

## Step 1: Login as Root

After your VPS provider gives you the IP and root password:

```bash
ssh root@YOUR_SERVER_IP
```

## Step 2: Update the System

```bash
apt update && apt upgrade -y
```

## Step 3: Create a Non-Root User

Replace `USERNAME` with your desired username:

```bash
# Create user (you'll be prompted for password)
adduser USERNAME

# Add user to sudo group
usermod -aG sudo USERNAME
```

## Step 4: Set Up SSH Key Authentication

### On your LOCAL machine (not the server):

If you don't have an SSH key yet:
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Copy your public key:
```bash
# macOS
cat ~/.ssh/id_ed25519.pub | pbcopy

# Linux
cat ~/.ssh/id_ed25519.pub
# (manually copy the output)
```

### On the SERVER (as root):

```bash
# Switch to new user
su - USERNAME

# Create SSH directory
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add your public key
nano ~/.ssh/authorized_keys
# Paste your public key, then Ctrl+X, Y, Enter to save

# Set correct permissions
chmod 600 ~/.ssh/authorized_keys

# Return to root
exit
```

## Step 5: Test New User Login (CRITICAL!)

> **Do NOT close your root session yet!**

Open a **NEW terminal window** and test:

```bash
ssh USERNAME@YOUR_SERVER_IP
```

Verify everything works:
```bash
# Should login without password prompt (using SSH key)

# Test sudo access
sudo whoami
# Should output: root
```

✅ If this works, you can close the root session.
❌ If this fails, use your root session to fix it.

## Step 6: Install Zappy the VPS Toolbox

As your new user:

```bash
# Install git (if not present)
sudo apt update && sudo apt install -y git

# Clone the toolbox
git clone https://github.com/KristjanPikhof/vps-toolbox.git /tmp/vps-toolbox
cd /tmp/vps-toolbox

# Run installer
sudo ./install.sh
```

## Step 7: Initial Server Hardening

Run Zappy:

```bash
vps-toolbox
```

### Recommended setup order:

#### 1. Firewall (Security first!)
```
Firewall Management → Allow service → SSH
Firewall Management → Allow service → HTTP
Firewall Management → Allow service → HTTPS
Firewall Management → Enable firewall
```

#### 2. SSH Hardening
```
Security Hardening → SSH Configuration → Apply recommended hardening
```

This will:
- Set `PermitRootLogin prohibit-password`
- Enable public key authentication
- Set stricter connection limits

#### 3. Fail2ban
```
Security Hardening → Fail2ban Setup → Install/Configure
```

#### 4. Automatic Security Updates
```
Security Hardening → Automatic Updates → Setup auto-updates
```

#### 5. Install Docker (optional)
```
Docker Setup → Install Docker
Docker Setup → Install Dockge
```

#### 6. Install Useful Tools (optional)
```
System Utilities → Install common tools → Install all missing packages
System Utilities → Setup zsh + oh-my-zsh
System Utilities → Install AiTermy
```

## Step 8: Add Your First Domain (optional)

```
Nginx Management → Add domain
```

Choose a template:
- **Reverse Proxy** - For backend services (Node.js, Python, etc.)
- **Reverse Proxy (WebSocket)** - For apps with real-time features
- **Static** - For static HTML/CSS/JS sites
- **PHP** - For PHP applications

Then add HTTPS:
```
Nginx Management → SSL Certificates → Add HTTPS to domain
```

---

## Security Checklist

After setup, verify these are configured:

- [ ] Non-root user created with sudo access
- [ ] SSH key authentication working
- [ ] Firewall enabled with SSH/HTTP/HTTPS allowed
- [ ] Root login disabled or key-only
- [ ] Password authentication disabled (optional but recommended)
- [ ] Fail2ban installed and running
- [ ] Automatic security updates enabled

---

## Quick Commands Reference

```bash
# Check firewall status
sudo ufw status

# Check fail2ban status
sudo fail2ban-client status

# Check SSH config
sudo sshd -T | grep -E "permitrootlogin|passwordauthentication|pubkeyauthentication"

# Check listening ports
sudo ss -tlnp

# View system resources
htop

# Check nginx status
sudo systemctl status nginx

# Test nginx config
sudo nginx -t

# View nginx error log
sudo tail -50 /var/log/nginx/error.log
```

---

## Troubleshooting

### Locked out of SSH?

Use your VPS provider's console/VNC access to:
1. Login as root via console
2. Fix SSH config: `nano /etc/ssh/sshd_config`
3. Restart SSH: `systemctl restart sshd`

### Firewall blocking access?

Via VPS console:
```bash
sudo ufw disable
# Fix your rules, then
sudo ufw enable
```

### Forgot sudo password?

Via VPS console as root:
```bash
passwd USERNAME
```

---

## Next Steps

- Set up your applications
- Configure domains and SSL certificates
- Set up backups (consider restic or borgbackup)
- Monitor your server with the built-in monitoring tools

---

**Need help?** Run `vps-toolbox` and let Zappy guide you!
