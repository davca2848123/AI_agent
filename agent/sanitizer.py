import re
import logging

logger = logging.getLogger(__name__)

def sanitize_output(text: str) -> str:
    """
    Sanitizes output by masking IP addresses (IPv4, IPv6) and MAC addresses for security.
    IPv4: Masks last two octets (e.g., 192.168.*.*).
    IPv6: Masks the second half of the address (e.g., 2001:db8:*:*:*:*).
    MAC: Masks the last 3 octets (e.g., 00:1A:2B:*:*:*).
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text with sensitive info masked
    """
    if not text:
        return text
    
    # 1. MAC Address Pattern
    # Matches XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX
    mac_pattern = r'\b([0-9A-Fa-f]{2})[:-]([0-9A-Fa-f]{2})[:-]([0-9A-Fa-f]{2})[:-]([0-9A-Fa-f]{2})[:-]([0-9A-Fa-f]{2})[:-]([0-9A-Fa-f]{2})\b'
    
    def replace_mac(match):
        # Keep first 3 octets, mask last 3
        sep = text[match.end(1):match.start(2)] # Detect separator
        return f"{match.group(1)}{sep}{match.group(2)}{sep}{match.group(3)}{sep}*{sep}*{sep}*"

    text = re.sub(mac_pattern, replace_mac, text)

    # 2. IPv6 Pattern
    # Explicit patterns to handle various compressed formats correctly without overlap
    ipv6_patterns = [
        r'\b([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}\b', # Full
        r'\b([0-9a-fA-F]{1,4}:){1}(:[0-9a-fA-F]{1,4}){1,6}\b', # 1 before ::
        r'\b([0-9a-fA-F]{1,4}:){2}(:[0-9a-fA-F]{1,4}){1,5}\b', # 2 before ::
        r'\b([0-9a-fA-F]{1,4}:){3}(:[0-9a-fA-F]{1,4}){1,4}\b', # 3 before ::
        r'\b([0-9a-fA-F]{1,4}:){4}(:[0-9a-fA-F]{1,4}){1,3}\b', # 4 before ::
        r'\b([0-9a-fA-F]{1,4}:){5}(:[0-9a-fA-F]{1,4}){1,2}\b', # 5 before ::
        r'\b([0-9a-fA-F]{1,4}:){6}(:[0-9a-fA-F]{1,4}){1}\b',   # 6 before ::
        r'\b([0-9a-fA-F]{1,4}:){1,7}:', # Ends with ::
        r':(:[0-9a-fA-F]{1,4}){1,7}\b', # Starts with ::
        r'::' # Just ::
    ]
    ipv6_pattern = "|".join(ipv6_patterns)
    
    def replace_ipv6(match):
        addr = match.group(0)
        if addr == "::": return "::*"
        
        # Split by colon
        parts = addr.split(':')
        
        # If it's a full address (8 parts), keep first 4
        if len(parts) >= 8:
            return ":".join(parts[:4]) + ":*:*:*:*"
            
        # For compressed addresses, keep roughly half
        keep_count = max(1, len(parts) // 2)
        
        # Reconstruct
        visible = ":".join(parts[:keep_count])
        
        if addr.startswith("::"):
            if visible == "":
                return "::*"
            elif visible.startswith(":"):
                return ":" + visible + ":*"
            else:
                return visible + ":*" # Should not happen for valid :: start
        elif addr.endswith("::"):
            return f"{visible}::*"
        elif "::" in addr:
             return f"{visible}:*"
        else:
             return f"{visible}:*"

    text = re.sub(ipv6_pattern, replace_ipv6, text)
    
    # 3. IPv4 Pattern - matches each octet separately
    ipv4_pattern = r'\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b'
    
    def replace_ipv4(match):
        """Replace last two octets with '*'."""
        # Keep first two octets visible, mask last two
        octet1 = match.group(1)
        octet2 = match.group(2)
        
        return f"{octet1}.{octet2}.*.*"
    
    text = re.sub(ipv4_pattern, replace_ipv4, text)
    
    return text
