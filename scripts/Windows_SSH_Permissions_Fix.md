# Windows SSH Config Permissions Fix

## Problem

When using SSH on Windows, you may encounter this warning:

```
Bad owner or permissions on C:\Users\Davča\.ssh\config
```

This occurs because Windows file permissions may be too broad, making SSH refuse to use the config file for security reasons.

---

## Solution

Use `icacls` (Windows built-in tool) to fix permissions.

### Step 1: Open PowerShell as Administrator

Right-click PowerShell → "Run as Administrator"

### Step 2: Remove Inheritance and Set Restrictive Permissions

```powershell
# Navigate to .ssh directory
cd C:\Users\Davča\.ssh

# Remove inheritance and grant only your user full control
icacls config /inheritance:r /grant:r "Davča:F"
```

**Explanation**:
- `/inheritance:r` - Remove inherited permissions
- `/grant:r "Davča:F"` - Grant full control ONLY to user "Davča"

### Step 3: Verify Permissions

```powershell
# Check current permissions
icacls config
```

**Expected output**:
```
config Davča:(F)
```

This means only your user has Full control (F), and no other users or groups have access.

---

## Alternative: One-Line Fix

```powershell
icacls C:\Users\Davča\.ssh\config /inheritance:r /grant:r "%USERNAME%:F"
```

This automatically uses your current Windows username.

---

## For Multiple SSH Files

If you have multiple files in `.ssh` directory (`id_rsa`, `known_hosts`, etc.), fix them all:

```powershell
# Fix all files in .ssh directory
cd C:\Users\Davča\.ssh
icacls * /inheritance:r /grant:r "Davča:F"
```

---

## Verify SSH Config Works

After fixing permissions:

```powershell
# Test SSH connection
ssh davca@192.168.1.200

# Should connect without "Bad owner or permissions" warning
```

---

## Troubleshooting

### "Access Denied" when running icacls

**Solution**: Run PowerShell as Administrator

### Still shows "Bad owner or permissions"

**Check file ownership**:
```powershell
# View detailed ownership
Get-Acl C:\Users\Davča\.ssh\config | Format-List
```

**Reset ownership if needed**:
```powershell
# Take ownership
takeown /F C:\Users\Davča\.ssh\config

# Then apply permissions again
icacls C:\Users\Davča\.ssh\config /inheritance:r /grant:r "Davča:F"
```

### Different username

Replace `Davča` with your actual Windows username:

```powershell
# Check your username
echo %USERNAME%

# Use it in command
icacls C:\Users\YourUsername\.ssh\config /inheritance:r /grant:r "YourUsername:F"
```

---

## Why This Is Needed

SSH requires strict permissions on configuration files for security:
- **Linux/Unix**: `chmod 600 ~/.ssh/config` (owner read/write only)
- **Windows**: Use `icacls` to achieve equivalent permissions

Without proper permissions, SSH refuses to use the config file to prevent unauthorized access.

---

## Permanent Fix

These permission changes are permanent. You only need to run this once per file.

If you create new files in `.ssh` directory, you'll need to apply the same permissions to them.

---

## Automated Script

Create a `.bat` file to automate this:

```batch
@echo off
echo Fixing SSH config permissions...
icacls C:\Users\Davča\.ssh\config /inheritance:r /grant:r "Davča:F"
echo Done!
pause
```

Save as `Fix_SSH_Permissions.bat` and run when needed.
