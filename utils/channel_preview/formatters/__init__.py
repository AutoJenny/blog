"""
Channel preview formatters package.

Provides per-channel formatter classes that implement a common interface:

    format(self, post_data: Dict[str, Any], mode: str = 'preview',
           variant: str = 'full') -> Dict[str, Any]

See `registry.py` for formatter lookup.
"""

