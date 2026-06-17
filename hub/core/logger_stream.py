import logging
import asyncio
import sys
from collections import deque

# Phase 5 / Slice 6A Story S6A.9 — readable operational query trace.
_TRACE_MAX_FIELD = 120


def format_query_trace(
    stage_log,
    intent=None,
    intent_confidence=None,
    answer_type=None,
    source_id=None,
    fallback_reason=None,
    compound_detected=False,
    secondary_intent=None,
):
    """Build one legible, ordered, bounded log line for a query: stage order +
    intent + outcome + key stable IDs. No raw article/answer text; each field is
    capped so a single line never dumps large payloads.
    """
    def _cap(v):
        s = str(v)
        return s if len(s) <= _TRACE_MAX_FIELD else s[:_TRACE_MAX_FIELD] + "…"

    parts = ["stages=" + ">".join(stage_log or [])]
    if intent is not None:
        conf = f"({intent_confidence:.2f})" if isinstance(intent_confidence, (int, float)) else ""
        parts.append(f"intent={_cap(intent)}{conf}")
    if compound_detected:
        parts.append(f"compound+{_cap(secondary_intent)}")
    if answer_type is not None:
        parts.append(f"outcome={_cap(answer_type)}")
    if source_id is not None:
        parts.append(f"src={_cap(source_id)}")
    if fallback_reason:
        parts.append(f"fallback={_cap(fallback_reason)}")
    return "[Trace] " + " | ".join(parts)

class MemoryStreamHandler(logging.Handler):
    def __init__(self, capacity=1000):
        super().__init__()
        self.capacity = capacity
        self.logs = deque(maxlen=capacity)
        self.listeners = set()
        # Basic matching formatter
        self.setFormatter(logging.Formatter('%(levelname)s:\t  %(message)s'))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.logs.append(msg)
            
            # Print to the real stdout so it goes to hub.log
            try:
                print(msg, file=sys.__stdout__, flush=True)
            except Exception:
                # Fallback for Windows consoles with limited encodings (e.g. cp1252).
                try:
                    if hasattr(sys.__stdout__, "buffer"):
                        sys.__stdout__.buffer.write((msg + "\n").encode("utf-8", "replace"))
                        sys.__stdout__.buffer.flush()
                except Exception:
                    pass

            # Notify all connected websockets
            for queue in list(self.listeners):
                try:
                    queue.put_nowait(msg)
                except asyncio.QueueFull:
                    pass
        except Exception:
            self.handleError(record)

    def add_listener(self, queue: asyncio.Queue):
        self.listeners.add(queue)
        
    def remove_listener(self, queue: asyncio.Queue):
        self.listeners.discard(queue)

stream_handler = MemoryStreamHandler()

class PrintToLogger:
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.buffer = ""

    def write(self, message):
        if message == '\n':
            return
        # If it ends with \n, log it immediately
        if message.endswith('\n'):
            self.logger.log(self.level, self.buffer + message.rstrip())
            self.buffer = ""
        else:
            self.buffer += message

    def flush(self):
        pass

    def isatty(self):
        """Required by libraries (e.g. transformers) that check stdout.isatty() for colored output."""
        return False

def setup_log_capture():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if stream_handler not in root.handlers:
        root.addHandler(stream_handler)

    # Prevent uvicorn/fastapi child loggers from propagating to root
    # (which would duplicate every message through the same handler).
    for name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
        child = logging.getLogger(name)
        child.propagate = False
        if stream_handler not in child.handlers:
            child.addHandler(stream_handler)

    print_logger = logging.getLogger("stdout")
    print_logger.propagate = False
    if stream_handler not in print_logger.handlers:
        print_logger.addHandler(stream_handler)
        sys.stdout = PrintToLogger(print_logger, logging.INFO)
        sys.stderr = PrintToLogger(print_logger, logging.ERROR)
