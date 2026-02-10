# CallbackHandler import removed as it is deprecated/removed in the installed version
print("Langfuse check: CallbackHandler is deprecated and removed from this check.")

try:
    from app.core.config import settings

    print(f"LANGFUSE_SECRET_KEY present: {bool(settings.LANGFUSE_SECRET_KEY)}")
    print(f"LANGFUSE_PUBLIC_KEY present: {bool(settings.LANGFUSE_PUBLIC_KEY)}")
    print(f"LANGFUSE_HOST: {settings.LANGFUSE_HOST}")
except Exception as e:
    print(f"Error loading settings: {e}")
