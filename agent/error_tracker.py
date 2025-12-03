"""
Error Tracker Module

Tracks runtime errors and provides analytics for debugging.
Used by !debug errors command.
"""

import time
import json
import os
import logging
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import traceback as tb

logger = logging.getLogger(__name__)

@dataclass
class ErrorEntry:
    """Individual error entry."""
    timestamp: float
    error_type: str  # "NameError", "AttributeError", etc.
    message: str
    traceback: str
    file: str
    line: int
    function: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)


class ErrorTracker:
    """Tracks and analyzes runtime errors."""
    
    MAX_ERRORS = 50  # Keep last 50 errors
    STORAGE_FILE = "error_tracker.json"
    CLEANUP_INTERVAL = 24 * 3600  # Clean old errors after 24h
    
    def __init__(self):
        self.recent_errors: List[ErrorEntry] = []
        self.error_counts: Dict[str, int] = {}
        self.last_cleaned = time.time()
        self._load()
    
    def log_error(self, exception: Exception, tb_str: str = None):
        """
        Log an error to the tracker.
        
        Args:
            exception: The exception object
            tb_str: Optional traceback string (if None, will extract from exception)
        """
        try:
            # Extract traceback info
            if tb_str is None:
                tb_str = tb.format_exc()
            
            # Parse traceback to get file, line, function
            tb_lines = tb_str.strip().split('\n')
            file_info = "unknown"
            line_num = 0
            func_name = "unknown"
            
            # Find the last "File" line (most relevant)
            for i, line in enumerate(tb_lines):
                if line.strip().startswith('File "'):
                    try:
                        # Parse: File "/path/to/file.py", line 123, in function_name
                        parts = line.split('"')
                        file_path = parts[1] if len(parts) > 1 else "unknown"
                        file_info = os.path.basename(file_path)
                        
                        # Extract line number
                        line_part = line.split("line ")[1].split(",")[0] if "line " in line else "0"
                        line_num = int(line_part)
                        
                        # Extract function name
                        if "in " in line:
                            func_name = line.split("in ")[1].strip()
                    except:
                        pass
            
            # Create error entry
            error_type = exception.__class__.__name__
            entry = ErrorEntry(
                timestamp=time.time(),
                error_type=error_type,
                message=str(exception),
                traceback=tb_str[-500:],  # Last 500 chars of traceback
                file=file_info,
                line=line_num,
                function=func_name
            )
            
            # Add to recent errors
            self.recent_errors.append(entry)
            
            # Trim if too many
            if len(self.recent_errors) > self.MAX_ERRORS:
                self.recent_errors = self.recent_errors[-self.MAX_ERRORS:]
            
            # Update counts
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            
            # Save to disk
            self._save()
            
            logger.debug(f"ErrorTracker: Logged {error_type} in {file_info}:{line_num}")
            
        except Exception as e:
            logger.error(f"ErrorTracker failed to log error: {e}")
    
    def get_recent(self, limit: int = 10, hours: int = 24) -> List[ErrorEntry]:
        """Get recent errors within time window."""
        cutoff = time.time() - (hours * 3600)
        recent = [e for e in self.recent_errors if e.timestamp > cutoff]
        return recent[-limit:]
    
    def get_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for debug command."""
        cutoff = time.time() - (hours * 3600)
        recent = [e for e in self.recent_errors if e.timestamp > cutoff]
        
        # Count by type
        type_counts = {}
        for err in recent:
            type_counts[err.error_type] = type_counts.get(err.error_type, 0) + 1
        
        # Last error time
        last_error_time = None
        if recent:
            last_error_time = recent[-1].timestamp
        
        return {
            "total": len(recent),
            "by_type": type_counts,
            "recent_errors": [e.to_dict() for e in recent[-10:]],
            "last_error": last_error_time
        }
    
    def get_recommendations(self) -> List[str]:
        """Generate recommendations based on error patterns."""
        recommendations = []
        recent = self.get_recent(limit=50, hours=24)
        
        if not recent:
            return ["No recent errors - system healthy!"]
        
        # Group by file and function
        file_errors = {}
        func_errors = {}
        
        for err in recent:
            key = f"{err.file}:{err.function}"
            file_errors[key] = file_errors.get(key, 0) + 1
            func_errors[err.function] = func_errors.get(err.function, 0) + 1
        
        # Find hotspots
        for location, count in sorted(file_errors.items(), key=lambda x: x[1], reverse=True)[:3]:
            if count > 1:
                recommendations.append(f"Review {location} ({count} similar errors)")
        
        # Type-specific recommendations
        type_counts = {}
        for err in recent:
            type_counts[err.error_type] = type_counts.get(err.error_type, 0) + 1
        
        for error_type, count in type_counts.items():
            if error_type == "NameError" and count > 1:
                recommendations.append("Check variable initialization in error-prone functions")
            elif error_type == "AttributeError" and count > 1:
                recommendations.append("Verify object method/attribute names")
            elif error_type == "KeyError" and count > 1:
                recommendations.append("Add defensive key checks in dictionaries")
        
        if not recommendations:
            recommendations.append("Consider adding defensive error handling")
        
        return recommendations
    
    def cleanup_old_errors(self):
        """Remove errors older than cleanup interval."""
        cutoff = time.time() - self.CLEANUP_INTERVAL
        self.recent_errors = [e for e in self.recent_errors if e.timestamp > cutoff]
        self.last_cleaned = time.time()
        self._save()
        logger.info(f"ErrorTracker: Cleaned old errors, {len(self.recent_errors)} remaining")
    
    def _save(self):
        """Persist to disk."""
        try:
            data = {
                "recent_errors": [e.to_dict() for e in self.recent_errors],
                "error_counts": self.error_counts,
                "last_cleaned": self.last_cleaned
            }
            with open(self.STORAGE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"ErrorTracker failed to save: {e}")
    
    def _load(self):
        """Load from disk."""
        try:
            if os.path.exists(self.STORAGE_FILE):
                with open(self.STORAGE_FILE, 'r') as f:
                    data = json.load(f)
                
                self.recent_errors = [ErrorEntry.from_dict(e) for e in data.get("recent_errors", [])]
                self.error_counts = data.get("error_counts", {})
                self.last_cleaned = data.get("last_cleaned", time.time())
                
                # Cleanup if needed
                if time.time() - self.last_cleaned > self.CLEANUP_INTERVAL:
                    self.cleanup_old_errors()
                
                logger.info(f"ErrorTracker: Loaded {len(self.recent_errors)} errors from disk")
        except Exception as e:
            logger.warning(f"ErrorTracker failed to load from disk: {e}")


# Global instance
_error_tracker = None

def get_error_tracker() -> ErrorTracker:
    """Get or create global ErrorTracker instance."""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker
