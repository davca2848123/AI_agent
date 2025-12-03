import os
import re
from datetime import datetime, timedelta

LOG_FILES = ["agent.log", "agent_tools.log"]

def cleanup_logs():
    # Calculate cutoff date (2 days ago at 00:00)
    cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=2)
    print(f"Deleting log entries older than: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for log_file in LOG_FILES:
        # Check if we are in the right directory, if not try to find the log file
        log_path = log_file
        if not os.path.exists(log_path):
            # Try looking in parent directory if running from scripts/
            if os.path.exists(os.path.join("..", log_file)):
                log_path = os.path.join("..", log_file)
            else:
                print(f"File {log_file} not found in current or parent directory. Skipping.")
                continue

        print(f"\nProcessing {log_path}...")
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            kept_lines = []
            deleted_count = 0
            
            # Process each line and check timestamp
            for line in lines:
                # Try to extract timestamp from log line
                # Expected format: YYYY-MM-DD HH:MM:SS or similar at the start of the line
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                
                if timestamp_match:
                    try:
                        log_timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                        
                        # Keep lines that are newer than or equal to cutoff date
                        if log_timestamp >= cutoff_date:
                            kept_lines.append(line)
                        else:
                            deleted_count += 1
                    except ValueError:
                        # If timestamp parsing fails, keep the line to be safe
                        kept_lines.append(line)
                else:
                    # If no timestamp found, keep the line (might be multi-line log entry)
                    kept_lines.append(line)
            
            print(f"Total lines: {total_lines}")
            print(f"Deleted lines: {deleted_count}")
            print(f"Kept lines: {len(kept_lines)}")
            
            # Write back the filtered logs
            with open(log_path, 'w', encoding='utf-8') as f:
                f.writelines(kept_lines)
                
            print(f"Done cleaning {log_file}")
            
        except Exception as e:
            print(f"Error processing {log_file}: {e}")
    
    print("\nAll log files processed.")

if __name__ == "__main__":
    cleanup_logs()
