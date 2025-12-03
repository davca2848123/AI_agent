import re
import logging

logger = logging.getLogger(__name__)

def sanitize_output(text: str) -> str:
    """
    Sanitizes output by masking IP addresses for security.
    Masks only the last two octets (e.g., 192.168.x.xxx).
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text with last two octets of IP addresses masked
    """
    if not text:
        return text
    
    # IPv4 pattern - matches each octet separately
    ipv4_pattern = r'\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b'
    
    def replace_ip(match):
        """Replace last two octets with 'x' preserving digit count."""
        # Keep first two octets visible, mask last two
        octet1 = match.group(1)
        octet2 = match.group(2)
        octet3 = match.group(3)
        octet4 = match.group(4)
        
        # Mask last two octets with 'x'
        masked_octet3 = 'x' * len(octet3)
        masked_octet4 = 'x' * len(octet4)
        
        return f"{octet1}.{octet2}.{masked_octet3}.{masked_octet4}"
    
    sanitized = re.sub(ipv4_pattern, replace_ip, text)
    
    return sanitized
