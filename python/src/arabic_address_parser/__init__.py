"""Arabic Address Parser: normalize, parse and compare Arabic / Franco-Arabic addresses."""
from .normalize import clean, key, normalize
from .parser import format_address, parse
from .similarity import is_same_address, similarity

__version__ = "0.1.0"
__all__ = ["clean", "key", "normalize", "parse", "format_address", "similarity", "is_same_address", "__version__"]
