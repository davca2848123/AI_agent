# RPI Sudoers Configuration - NOPASSWD Setup

## Overview
This guide explains how to configure sudo NOPASSWD for the RPI AI agent, allowing it to execute specific system commands without requiring a password.

⚠️ **SECURITY NOTE**: We configure NOPASSWD only for **specific commands** that the agent needs, not for all commands. This limits security risk.

---

## What Commands Need NOPASSWD?

The agent needs passwordless sudo access for:

1. **SWAP Management**:
   - `/sbin/swapon` - Enable swap
   - `/sbin/swapoff` - Disable swap

2. **Service Management** (optional):
   - `/bin/systemctl restart rpi_agent` - Self-restart capability
   - `/bin/systemctl status rpi_agent` - Check own status

---

## Installation Steps

### Step 1: SSH to RPI

```bash
ssh davca@192.168.1.200
```

### Step 2: Create Sudoers Configuration File

```bash
# Create a dedicated sudoers file for the agent
sudo nano /etc/sudoers.d/rpi_agent
```

### Step 3: Add NOPASSWD Rules

**RECOMMENDED: Full sudo access (Discord authorization via !cmd handles security)**

```
# RPI AI Agent - Passwordless sudo for all commands
# Security is handled by Discord admin authorization in !cmd command
davca ALL=(ALL) NOPASSWD: ALL
```

> **Security Note**: This allows passwordless sudo for ALL commands, but security is enforced on Discord side:
> - `!cmd sudo ...` requires admin user ID authorization
> - Only configured admins in `config_settings.ADMIN_USER_IDS` can execute sudo commands
> - Non-admins get "❌ Nedostatečná oprávnění" response

---

**Alternative Options** (if you prefer more restriction):

**Option A: SWAP + Service management only**
```
# Limited to specific commands
davca ALL=(ALL) NOPASSWD: /sbin/swapon, /sbin/swapoff, /bin/systemctl *
```

**Option B: SWAP only (most restrictive)**
```
# Only SWAP management
davca ALL=(ALL) NOPASSWD: /sbin/swapon, /sbin/swapoff
```

### Step 4: Set Correct Permissions

```bash
# Set correct permissions (IMPORTANT for security)
sudo chmod 0440 /etc/sudoers.d/rpi_agent

# Verify the file has correct permissions
ls -l /etc/sudoers.d/rpi_agent
# Should show: -r--r----- 1 root root
```

### Step 5: Test Configuration

```bash
# Test swap commands (should NOT ask for password)
sudo swapon --show
sudo systemctl status rpi_agent

# If password is requested, check syntax in /etc/sudoers.d/rpi_agent
```

---

## Verification

After configuration, test that sudo works without password:

```bash
# This should work WITHOUT prompting for password
sudo swapon -s

# This should also work
sudo swapoff -a
```

If it still asks for password:
1. Check `/etc/sudoers.d/rpi_agent` syntax with: `sudo visudo -cf /etc/sudoers.d/rpi_agent`
2. Ensure permissions are `0440`
3. Restart SSH session

---

## Security Considerations

### Two-Layer Security Model

**Layer 1: Discord Authorization (Primary)**
- `!cmd` command checks `config_settings.ADMIN_USER_IDS`
- Only admins can execute commands with `sudo`
- Non-admins receive: `❌ Nedostatečná oprávnění`
- Authorization is checked BEFORE command execution

**Layer 2: RPI NOPASSWD (Convenience)**
- Allows agent to execute sudo without password prompt
- Does NOT bypass Discord authorization
- Simplifies automated tasks (SWAP management, service control)

### Why This Is Safe

✅ **SAFE with Discord authorization**:
- Discord bot only accepts `!cmd sudo ...` from configured admins
- Agent code validates user ID before executing ANY command
- Logging tracks all sudo command executions
- NOPASSWD just removes password prompt for authorized commands

⚠️ **What to avoid**:
- Don't share RPI direct SSH access with untrusted users
- Don't run agent with a user account that has sensitive data
- Monitor `/var/log/auth.log` for unexpected sudo usage

### Without NOPASSWD vs With NOPASSWD

**Without NOPASSWD (problematic for automation)**:
```bash
# Agent tries to execute sudo command
$ sudo swapon /swapfile
[sudo] password for davca: █  # <-- Agent can't provide password automatically
# Command fails, SWAP activation fails
```

**With NOPASSWD (works seamlessly)**:
```bash
# Agent executes sudo command
$ sudo swapon /swapfile
# Success! No password prompt
# SWAP activated automatically
```

---

## Example: How Authorization Works

### Scenario 1: Admin executes sudo command
```
Discord User: @Admin (ID: 123456789)
Command: !cmd sudo systemctl restart rpi_agent

Agent checks: Is user ID in ADMIN_USER_IDS? ✅ YES
Agent executes: sudo systemctl restart rpi_agent
RPI: No password needed (NOPASSWD configured)
Result: ✅ Service restarted
```

### Scenario 2: Non-admin tries sudo command
```
Discord User: @RandomUser (ID: 987654321)
Command: !cmd sudo systemctl restart rpi_agent

Agent checks: Is user ID in ADMIN_USER_IDS? ❌ NO
Agent responds: ❌ Nedostatečná oprávnění
RPI: Command never executed
Result: ❌ Access denied at Discord layer
```

---

## Troubleshooting

### "sudo: /etc/sudoers.d/rpi_agent is world writable"

**Fix permissions:**
```bash
sudo chmod 0440 /etc/sudoers.d/rpi_agent
```

### "sudo: parse error in /etc/sudoers.d/rpi_agent"

**Check syntax:**
```bash
sudo visudo -cf /etc/sudoers.d/rpi_agent
```

Fix any syntax errors and save.

### Still asks for password

1. Verify user name matches: `whoami` should show `davca`
2. Check absolute command paths: `which swapon` should show `/sbin/swapon`
3. Restart SSH session: `exit` and reconnect

---

## Removing NOPASSWD (if needed)

To remove passwordless sudo access:

```bash
# Remove the configuration file
sudo rm /etc/sudoers.d/rpi_agent

# Or comment out lines in the file
sudo nano /etc/sudoers.d/rpi_agent
# Add # at the start of each line
```

---

## Example Agent Usage

After configuration, the agent can execute:

```python
# In Python code (agent/commands.py)
import subprocess

# Enable SWAP - no password needed
subprocess.run(['sudo', 'swapon', '/swapfile'], check=True)

# Disable SWAP - no password needed
subprocess.run(['sudo', 'swapoff', '/swapfile'], check=True)

# Restart service - no password needed (if configured)
subprocess.run(['sudo', 'systemctl', 'restart', 'rpi_agent'], check=True)
```

---

## What Does NOPASSWD Mean?

**Without NOPASSWD**:
```bash
$ sudo swapon -s
[sudo] password for davca: █  # <-- Asks for password
```

**With NOPASSWD**:
```bash
$ sudo swapon -s
Filename    Type    Size      Used    Priority
/swapfile   file    2097148   0       -2
# <-- No password prompt!
```

---

## Recommended Configuration

For the RPI AI Agent, use **Option A (Minimal)**:

```bash
# /etc/sudoers.d/rpi_agent
davca ALL=(ALL) NOPASSWD: /sbin/swapon, /sbin/swapoff
```

This provides:
- ✅ Agent can manage SWAP without password
- ✅ Minimal security risk
- ✅ Agent cannot execute other dangerous commands
- ✅ Explicit command paths prevent abuse

---

## Additional Notes

- Changes take effect immediately (no restart needed)
- SSH session must be restarted to see changes
- Monitor `/var/log/auth.log` for sudo usage:
  ```bash
  sudo tail -f /var/log/auth.log | grep sudo
  ```
