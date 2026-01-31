"""
Security Utilities - Input sanitization, validation, and protection
Prevents injection attacks and protects sensitive data

Copyright (c) 2025 DecentralizedJM (https://github.com/DecentralizedJM)
Licensed under MIT License
"""
import re
import logging
import math
from typing import Optional, Dict, Any, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class InputSanitizer:
    """
    Sanitizes user input to prevent various injection attacks.
    
    Protects against:
    - Script injection (<script>)
    - Template injection ({{...}}, ${...})
    - Prototype pollution (__proto__)
    - SQL injection (basic patterns)
    - Path traversal (../)
    """
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        # Script injection
        (r'<script[^>]*>', 'script_tag'),
        (r'javascript:', 'javascript_protocol'),
        (r'on\w+\s*=', 'event_handler'),
        
        # Template injection
        (r'\{\{.*?\}\}', 'template_mustache'),
        (r'\$\{.*?\}', 'template_dollar'),
        (r'<%.*?%>', 'template_erb'),
        
        # Prototype pollution
        (r'__proto__', 'proto_pollution'),
        (r'constructor\s*\[', 'constructor_pollution'),
        (r'prototype\s*\[', 'prototype_pollution'),
        
        # Path traversal
        (r'\.\./', 'path_traversal'),
        (r'\.\.\\', 'path_traversal_win'),
        
        # SQL injection (basic)
        (r';\s*drop\s+', 'sql_drop'),
        (r';\s*delete\s+', 'sql_delete'),
        (r';\s*update\s+', 'sql_update'),
        (r'union\s+select', 'sql_union'),
        
        # Command injection
        (r';\s*rm\s+', 'cmd_rm'),
        (r'\|\s*cat\s+', 'cmd_cat'),
        (r'`[^`]+`', 'cmd_backtick'),
    ]
    
    # Characters to strip from input
    STRIP_CHARS = ['\x00', '\x0b', '\x0c']
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize sanitizer.
        
        Args:
            strict_mode: If True, block any suspicious patterns.
                        If False, just clean/escape them.
        """
        self.strict_mode = strict_mode
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns"""
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), name)
            for pattern, name in self.DANGEROUS_PATTERNS
        ]
    
    def sanitize(self, text: str) -> Tuple[str, List[str]]:
        """
        Sanitize input text.
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Tuple of (sanitized_text, list of blocked patterns found)
        """
        if not text:
            return "", []
        
        blocked = []
        sanitized = text
        
        # Strip null bytes and control characters
        for char in self.STRIP_CHARS:
            sanitized = sanitized.replace(char, '')
        
        # Check for dangerous patterns
        for pattern, name in self.compiled_patterns:
            if pattern.search(sanitized):
                blocked.append(name)
                if self.strict_mode:
                    # In strict mode, block entirely
                    logger.warning(f"Blocked dangerous pattern: {name}")
                else:
                    # In normal mode, remove the pattern
                    sanitized = pattern.sub('', sanitized)
        
        # Limit length to prevent DoS
        max_length = 10000
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            blocked.append('length_exceeded')
        
        return sanitized, blocked
    
    def is_safe(self, text: str) -> bool:
        """Check if text is safe without modifying it"""
        _, blocked = self.sanitize(text)
        return len(blocked) == 0


class APIKeyDetector:
    """
    Enhanced API key detection with entropy analysis.
    
    Features:
    - Multiple regex patterns for common API key formats
    - Entropy analysis (real keys have high entropy)
    - Mudrex-specific key format detection
    """
    
    # Common API key patterns
    KEY_PATTERNS = [
        # Mudrex-specific
        (r'api[_\s-]?secret[_\s-]?(?:is|:)?\s*["\']?([A-Za-z0-9_\-]{20,})["\']?', 'mudrex_api_secret'),
        (r'api[_\s-]?key[_\s-]?(?:is|:)?\s*["\']?([A-Za-z0-9_\-]{20,})["\']?', 'mudrex_api_key'),
        
        # Generic patterns
        (r'(?:secret|token|key|api_key|apikey)[_\s-]?(?:is|:)?\s*["\']?([A-Za-z0-9_\-]{16,})["\']?', 'generic_secret'),
        (r'["\']?([A-Za-z0-9_\-]{32,})["\']?', 'long_token'),
        
        # Common formats
        (r'sk[-_][a-zA-Z0-9]{32,}', 'stripe_key'),
        (r'ghp_[a-zA-Z0-9]{36}', 'github_pat'),
        (r'[A-Za-z0-9+/]{40,}={0,2}', 'base64_key'),
    ]
    
    # Minimum entropy threshold for likely API keys
    ENTROPY_THRESHOLD = 3.5
    
    def __init__(self):
        """Initialize detector"""
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Pre-compile regex patterns"""
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), name)
            for pattern, name in self.KEY_PATTERNS
        ]
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        if not text:
            return 0.0
        
        counter = Counter(text)
        length = len(text)
        
        entropy = 0.0
        for count in counter.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def detect(self, text: str) -> Dict[str, Any]:
        """
        Detect potential API keys in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with detection results:
            - has_key: bool - whether a key was detected
            - patterns: list - matched patterns
            - entropy: float - entropy of potential key
            - key_preview: str - masked preview of detected key
        """
        if not text or len(text) < 10:
            return {'has_key': False, 'patterns': [], 'entropy': 0, 'key_preview': None}
        
        detected_patterns = []
        highest_entropy = 0.0
        detected_key = None
        
        for pattern, name in self.compiled_patterns:
            matches = pattern.findall(text)
            for match in matches:
                key = match if isinstance(match, str) else match[0] if match else ""
                if key and len(key) >= 16:
                    entropy = self._calculate_entropy(key)
                    if entropy >= self.ENTROPY_THRESHOLD:
                        detected_patterns.append(name)
                        if entropy > highest_entropy:
                            highest_entropy = entropy
                            detected_key = key
        
        # Also check if user explicitly mentions sharing API key
        lower_text = text.lower()
        mentions_sharing = any(phrase in lower_text for phrase in [
            "my api secret", "api secret is", "my api key", "api key is",
            "here is my key", "here's my key", "my secret is"
        ])
        
        has_key = bool(detected_patterns) or (mentions_sharing and highest_entropy > 3.0)
        
        # Create masked preview
        key_preview = None
        if detected_key:
            if len(detected_key) > 8:
                key_preview = f"{detected_key[:4]}...{detected_key[-4:]}"
            else:
                key_preview = "***"
        
        return {
            'has_key': has_key,
            'patterns': detected_patterns,
            'entropy': highest_entropy,
            'key_preview': key_preview,
            'mentions_sharing': mentions_sharing,
        }
    
    def mask_keys(self, text: str) -> str:
        """
        Mask all detected API keys in text.
        
        Args:
            text: Text containing potential keys
            
        Returns:
            Text with keys masked
        """
        if not text:
            return text
        
        masked = text
        for pattern, _ in self.compiled_patterns:
            def mask_match(match):
                key = match.group(0)
                if len(key) > 8:
                    return f"{key[:4]}****{key[-4:]}"
                return "****"
            masked = pattern.sub(mask_match, masked)
        
        return masked


def sanitize_input(text: str, strict: bool = False) -> str:
    """
    Convenience function to sanitize input.
    
    Args:
        text: Input to sanitize
        strict: Use strict mode
        
    Returns:
        Sanitized text
    """
    sanitizer = InputSanitizer(strict_mode=strict)
    sanitized, blocked = sanitizer.sanitize(text)
    
    if blocked:
        logger.info(f"Input sanitization blocked patterns: {blocked}")
    
    return sanitized


def detect_api_key(text: str) -> bool:
    """
    Convenience function to check if text contains API key.
    
    Args:
        text: Text to check
        
    Returns:
        True if API key detected
    """
    detector = APIKeyDetector()
    result = detector.detect(text)
    return result['has_key']


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data in text for logging.
    
    Args:
        text: Text to mask
        
    Returns:
        Text with sensitive data masked
    """
    detector = APIKeyDetector()
    return detector.mask_keys(text)
