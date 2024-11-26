import logging
import sys
import os

# Configure logging (This will apply to all modules that import logging)
log_level = logging.INFO if os.getenv("VERCEL_ENV") else logging.DEBUG

logging.basicConfig(
    stream=sys.stderr,
    level=logging.DEBUG,
    # level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
