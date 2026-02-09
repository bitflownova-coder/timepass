"""
Error Parser - Analyzes stack traces and error messages
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from config import settings

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class StackFrame:
    """Single frame in a stack trace"""
    file_path: Optional[str]
    line_number: Optional[int]
    function_name: Optional[str]
    code_context: Optional[str]
    is_user_code: bool = True  # vs library code


@dataclass
class ParsedError:
    """Parsed error information"""
    error_type: str
    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    stack_frames: List[StackFrame] = field(default_factory=list)
    related_files: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    raw_output: str = ""
    language: Optional[str] = None


class ErrorParser:
    """Parses error messages and stack traces from various languages"""
    
    # Python patterns
    PYTHON_TRACEBACK_START = re.compile(r'^Traceback \(most recent call last\):')
    PYTHON_FRAME = re.compile(r'^\s+File "([^"]+)", line (\d+), in (.+)$')
    PYTHON_CODE_LINE = re.compile(r'^\s{4}(.+)$')
    PYTHON_ERROR = re.compile(r'^(\w+Error|\w+Exception|KeyboardInterrupt): (.*)$')
    PYTHON_SYNTAX_ERROR = re.compile(r'^\s+File "([^"]+)", line (\d+)')
    
    # JavaScript/Node patterns
    JS_ERROR = re.compile(r'^(\w+Error): (.+)$')
    JS_FRAME = re.compile(r'^\s+at (?:(.+?) \()?([^:]+):(\d+):(\d+)\)?$')
    JS_ASYNC_FRAME = re.compile(r'^\s+at async (.+)$')
    
    # TypeScript patterns
    TS_ERROR = re.compile(r'^(.+)\((\d+),(\d+)\): error TS\d+: (.+)$')
    
    # Java patterns
    JAVA_ERROR = re.compile(r'^([\w.]+(?:Exception|Error)): (.*)$')
    JAVA_FRAME = re.compile(r'^\s+at ([\w.$]+)\(([\w.]+):(\d+)\)$')
    
    # Go patterns
    GO_PANIC = re.compile(r'^panic: (.+)$')
    GO_FRAME = re.compile(r'^([\w./]+):(\d+)')
    
    # Rust patterns
    RUST_ERROR = re.compile(r'^error\[E\d+\]: (.+)$')
    RUST_LOCATION = re.compile(r'^\s*--> (.+):(\d+):(\d+)$')
    
    # Generic patterns
    GENERIC_FILE_LINE = re.compile(r'([^\s:]+):(\d+)(?::(\d+))?')
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path) if workspace_path else None
    
    def _is_user_code(self, file_path: str) -> bool:
        """Check if file is user code (not library)"""
        if not file_path:
            return False
        
        library_indicators = [
            'site-packages', 'node_modules', 'vendor',
            '/usr/lib/', '/usr/local/lib/', 'Python3',
            '.cargo', 'go/pkg', '.rustup'
        ]
        
        return not any(ind in file_path for ind in library_indicators)
    
    def _detect_language(self, error_text: str) -> Optional[str]:
        """Detect programming language from error text"""
        if self.PYTHON_TRACEBACK_START.search(error_text):
            return "python"
        if "at Object.<anonymous>" in error_text or "at Module._compile" in error_text:
            return "javascript"
        if "error TS" in error_text:
            return "typescript"
        if "Exception in thread" in error_text or ".java:" in error_text:
            return "java"
        if "panic:" in error_text and "goroutine" in error_text:
            return "go"
        if "error[E" in error_text:
            return "rust"
        return None
    
    def parse(self, error_text: str) -> ParsedError:
        """Parse error text and return structured information"""
        language = self._detect_language(error_text)
        
        if language == "python":
            return self._parse_python(error_text)
        elif language in ("javascript", "typescript"):
            return self._parse_javascript(error_text)
        elif language == "java":
            return self._parse_java(error_text)
        elif language == "go":
            return self._parse_go(error_text)
        elif language == "rust":
            return self._parse_rust(error_text)
        else:
            return self._parse_generic(error_text)
    
    def _parse_python(self, error_text: str) -> ParsedError:
        """Parse Python traceback"""
        lines = error_text.strip().split('\n')
        frames = []
        error_type = "UnknownError"
        message = ""
        current_frame = None
        
        for i, line in enumerate(lines):
            # Check for frame
            frame_match = self.PYTHON_FRAME.match(line)
            if frame_match:
                if current_frame:
                    frames.append(current_frame)
                current_frame = StackFrame(
                    file_path=frame_match.group(1),
                    line_number=int(frame_match.group(2)),
                    function_name=frame_match.group(3),
                    code_context=None,
                    is_user_code=self._is_user_code(frame_match.group(1))
                )
                continue
            
            # Check for code context
            if current_frame and self.PYTHON_CODE_LINE.match(line):
                current_frame.code_context = line.strip()
                continue
            
            # Check for error line
            error_match = self.PYTHON_ERROR.match(line)
            if error_match:
                error_type = error_match.group(1)
                message = error_match.group(2)
        
        if current_frame:
            frames.append(current_frame)
        
        # Get primary error location
        user_frames = [f for f in frames if f.is_user_code]
        primary_frame = user_frames[-1] if user_frames else (frames[-1] if frames else None)
        
        # Find related files
        related = list(set(f.file_path for f in frames if f.file_path and f.is_user_code))
        
        return ParsedError(
            error_type=error_type,
            message=message,
            file_path=primary_frame.file_path if primary_frame else None,
            line_number=primary_frame.line_number if primary_frame else None,
            stack_frames=frames,
            related_files=related[:settings.max_related_files],
            suggestions=self._get_python_suggestions(error_type, message),
            raw_output=error_text,
            language="python"
        )
    
    def _parse_javascript(self, error_text: str) -> ParsedError:
        """Parse JavaScript/Node.js error"""
        lines = error_text.strip().split('\n')
        frames = []
        error_type = "Error"
        message = ""
        
        for line in lines:
            # Check for error line
            error_match = self.JS_ERROR.match(line)
            if error_match:
                error_type = error_match.group(1)
                message = error_match.group(2)
                continue
            
            # Check for stack frame
            frame_match = self.JS_FRAME.match(line)
            if frame_match:
                frames.append(StackFrame(
                    file_path=frame_match.group(2),
                    line_number=int(frame_match.group(3)),
                    function_name=frame_match.group(1),
                    code_context=None,
                    is_user_code=self._is_user_code(frame_match.group(2))
                ))
        
        user_frames = [f for f in frames if f.is_user_code]
        primary_frame = user_frames[0] if user_frames else (frames[0] if frames else None)
        related = list(set(f.file_path for f in frames if f.file_path and f.is_user_code))
        
        return ParsedError(
            error_type=error_type,
            message=message,
            file_path=primary_frame.file_path if primary_frame else None,
            line_number=primary_frame.line_number if primary_frame else None,
            stack_frames=frames,
            related_files=related[:settings.max_related_files],
            suggestions=self._get_js_suggestions(error_type, message),
            raw_output=error_text,
            language="javascript"
        )
    
    def _parse_java(self, error_text: str) -> ParsedError:
        """Parse Java exception"""
        # Similar structure to JS parser
        lines = error_text.strip().split('\n')
        frames = []
        error_type = "Exception"
        message = ""
        
        for line in lines:
            error_match = self.JAVA_ERROR.match(line)
            if error_match:
                error_type = error_match.group(1)
                message = error_match.group(2)
                continue
            
            frame_match = self.JAVA_FRAME.match(line)
            if frame_match:
                frames.append(StackFrame(
                    file_path=frame_match.group(2),
                    line_number=int(frame_match.group(3)),
                    function_name=frame_match.group(1),
                    code_context=None,
                    is_user_code=self._is_user_code(frame_match.group(2))
                ))
        
        primary_frame = frames[0] if frames else None
        
        return ParsedError(
            error_type=error_type,
            message=message,
            file_path=primary_frame.file_path if primary_frame else None,
            line_number=primary_frame.line_number if primary_frame else None,
            stack_frames=frames,
            raw_output=error_text,
            language="java"
        )
    
    def _parse_go(self, error_text: str) -> ParsedError:
        """Parse Go panic/error"""
        lines = error_text.strip().split('\n')
        message = ""
        
        for line in lines:
            panic_match = self.GO_PANIC.match(line)
            if panic_match:
                message = panic_match.group(1)
                break
        
        return ParsedError(
            error_type="panic",
            message=message,
            raw_output=error_text,
            language="go"
        )
    
    def _parse_rust(self, error_text: str) -> ParsedError:
        """Parse Rust compiler error"""
        lines = error_text.strip().split('\n')
        message = ""
        file_path = None
        line_number = None
        
        for line in lines:
            error_match = self.RUST_ERROR.match(line)
            if error_match:
                message = error_match.group(1)
                continue
            
            loc_match = self.RUST_LOCATION.match(line)
            if loc_match and not file_path:
                file_path = loc_match.group(1)
                line_number = int(loc_match.group(2))
        
        return ParsedError(
            error_type="CompileError",
            message=message,
            file_path=file_path,
            line_number=line_number,
            raw_output=error_text,
            language="rust"
        )
    
    def _parse_generic(self, error_text: str) -> ParsedError:
        """Generic error parsing"""
        # Try to extract file:line references
        matches = self.GENERIC_FILE_LINE.findall(error_text)
        
        file_path = None
        line_number = None
        if matches:
            file_path = matches[0][0]
            line_number = int(matches[0][1])
        
        # First line is usually the error message
        lines = error_text.strip().split('\n')
        message = lines[0] if lines else error_text
        
        return ParsedError(
            error_type="Error",
            message=message,
            file_path=file_path,
            line_number=line_number,
            raw_output=error_text
        )
    
    def _get_python_suggestions(self, error_type: str, message: str) -> List[str]:
        """Get suggestions for Python errors"""
        suggestions = []
        
        if error_type == "ImportError" or error_type == "ModuleNotFoundError":
            module = re.search(r"'(\w+)'", message)
            if module:
                suggestions.append(f"Install missing module: pip install {module.group(1)}")
                suggestions.append("Check if virtual environment is activated")
        
        elif error_type == "AttributeError":
            suggestions.append("Check if object is None before accessing attribute")
            suggestions.append("Verify the attribute name spelling")
        
        elif error_type == "TypeError":
            if "NoneType" in message:
                suggestions.append("A variable is None when it shouldn't be")
            if "argument" in message:
                suggestions.append("Check function call arguments match signature")
        
        elif error_type == "KeyError":
            suggestions.append("Check if key exists before accessing: dict.get(key)")
            suggestions.append("Verify dictionary key spelling")
        
        elif error_type == "IndexError":
            suggestions.append("Check list/array bounds before accessing")
            suggestions.append("Verify the collection is not empty")
        
        return suggestions
    
    def _get_js_suggestions(self, error_type: str, message: str) -> List[str]:
        """Get suggestions for JavaScript errors"""
        suggestions = []
        
        if error_type == "TypeError":
            if "undefined" in message:
                suggestions.append("Check if variable is defined before use")
                suggestions.append("Add null/undefined check")
            if "is not a function" in message:
                suggestions.append("Verify the function exists and is imported")
        
        elif error_type == "ReferenceError":
            suggestions.append("Variable not declared - check imports/declarations")
        
        elif error_type == "SyntaxError":
            suggestions.append("Check for missing brackets, semicolons, or quotes")
        
        return suggestions
    
    def get_context(self, file_path: str, line_number: int, context_lines: int = None) -> Optional[str]:
        """Get code context around error line"""
        context_lines = context_lines or settings.max_context_lines
        
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            lines = path.read_text().split('\n')
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)
            
            context = []
            for i in range(start, end):
                marker = ">>> " if i == line_number - 1 else "    "
                context.append(f"{i + 1:4d} {marker}{lines[i]}")
            
            return '\n'.join(context)
        except Exception:
            return None


# Global parser instance
error_parser = ErrorParser()
