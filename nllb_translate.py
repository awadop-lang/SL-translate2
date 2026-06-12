"""
NLLB Model - DISABLED by default to save resources

This module is intentionally minimal. NLLB model loading has been disabled
to prevent resource exhaustion on Hugging Face Spaces.

Use instead:
- Engine 1: Groq API (recommended, no local resources)
- Engine 0: DeepL API (if key available)
"""

async def translate_nllb(text: str, source_lang=None, target_lang=None, max_length: int = 256) -> str:
    """
    NLLB is disabled to save resources.
    Returns None to trigger fallback to Groq/DeepL.
    """
    print("[NLLB] Disabled - use Groq or DeepL instead")
    return None
