import sys
import os
import logging

# Add parent directory to path to import agent modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.memory import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting memory cleanup...")
    
    try:
        # Initialize memory store
        memory = VectorStore(db_path="agent_memory.db")
        
        # Execute cleanups
        boredom_count = memory.delete_boredom_memories()
        error_count = memory.delete_error_memories()
        
        total_count = boredom_count + error_count
        
        logger.info(f"Cleanup complete:")
        logger.info(f"  - Boredom memories removed: {boredom_count}")
        logger.info(f"  - Error memories removed: {error_count}")
        logger.info(f"  - Total removed: {total_count}")
        
        memory.close()
        
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")

if __name__ == "__main__":
    main()
