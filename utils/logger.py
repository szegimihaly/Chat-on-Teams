import logging
import sys
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama
init()

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'chat_timestamp': Fore.CYAN,
        'chat_user': Fore.GREEN,
        'chat_ai': Fore.MAGENTA,
        'chat_system': Fore.YELLOW,
        'error': Fore.RED,
    }

    def format(self, record):
        # Preserve newlines in chat messages but handle other logs
        if hasattr(record, 'is_chat') and record.is_chat:
            if hasattr(record, 'color'):
                return f"{self.COLORS.get(record.color, '')}{str(record.msg)}{Style.RESET_ALL}"
            return str(record.msg)
        if record.msg:
            record.msg = str(record.msg).replace('\n', '\\n')
        return super().format(record)

class DebugFormatter(logging.Formatter):
    def format(self, record):
        # Always escape newlines in debug logs
        if record.msg:
            record.msg = str(record.msg).replace('\n', '\\n')
        return super().format(record)

def setup_logger(debug=False):
    # Create logger
    logger = logging.getLogger('teams_chat')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create console handler with colored formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = ColoredFormatter('%(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    if debug:
        # Create debug file handler with escaped newlines
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        debug_handler = logging.FileHandler(f'debug_{timestamp}.log')
        debug_handler.setLevel(logging.DEBUG)
        debug_format = DebugFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        debug_handler.setFormatter(debug_format)
        logger.addHandler(debug_handler)
        
        logger.debug("Debug logging enabled")
    
    # Add chat logging methods
    def chat_log(self, msg, color='chat_user'):
        extra = {'is_chat': True, 'color': color}
        self.info(msg, extra=extra)
        if debug:
            self.debug(f"CHAT: {msg}")
    
    def error_log(self, msg):
        extra = {'is_chat': True, 'color': 'error'}
        self.error(msg, extra=extra)
        if debug:
            self.debug(f"ERROR: {msg}")
    
    logger.chat = chat_log.__get__(logger)
    logger.error_colored = error_log.__get__(logger)
    return logger