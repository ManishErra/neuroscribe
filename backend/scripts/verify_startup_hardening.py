import sys
import os
from pathlib import Path

# Add backend directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import database first to trigger load_dotenv
import database

# Save original environment values
original_secret = os.environ.get("JWT_SECRET")
original_algorithm = os.environ.get("JWT_ALGORITHM")
original_expire = os.environ.get("JWT_EXPIRE_MINUTES")

# Clear environment values so they don't interfere
if "JWT_SECRET" in os.environ:
    del os.environ["JWT_SECRET"]
if "JWT_ALGORITHM" in os.environ:
    del os.environ["JWT_ALGORITHM"]
if "JWT_EXPIRE_MINUTES" in os.environ:
    del os.environ["JWT_EXPIRE_MINUTES"]

# Mock os.getenv to isolate testing
original_getenv = os.getenv

def make_mock_getenv(secret_val, algo_val, expire_val="480"):
    def mock_getenv(key, default=None):
        if key == "JWT_SECRET":
            return secret_val
        if key == "JWT_ALGORITHM":
            return algo_val
        if key == "JWT_EXPIRE_MINUTES":
            return expire_val
        return original_getenv(key, default)
    return mock_getenv

def force_cleanup_auth_utils():
    if "auth_utils" in sys.modules:
        del sys.modules["auth_utils"]

print("\n--- Starting Programmatic Startup Hardening Tests (SEC-01B) ---")

# Test Case 1: Missing JWT_SECRET
print("Test Case 1: Missing JWT_SECRET startup failure...", end=" ")
force_cleanup_auth_utils()
os.getenv = make_mock_getenv(None, "HS256")
try:
    import auth_utils
    print("FAILED (no exception raised)")
    sys.exit(1)
except RuntimeError as e:
    if "JWT_SECRET environment variable is missing" in str(e):
        print("PASSED (RuntimeError raised correctly)")
    else:
        print(f"FAILED (Unexpected RuntimeError: {e})")
        sys.exit(1)
except Exception as e:
    print(f"FAILED (Unexpected exception type: {type(e).__name__}: {e})")
    sys.exit(1)

# Test Case 2: Short JWT_SECRET (< 32 chars)
print("Test Case 2: Short JWT_SECRET startup failure...", end=" ")
force_cleanup_auth_utils()
os.getenv = make_mock_getenv("too-short-secret-key", "HS256")
try:
    import auth_utils
    print("FAILED (no exception raised)")
    sys.exit(1)
except RuntimeError as e:
    if "JWT_SECRET is too weak" in str(e):
        print("PASSED (RuntimeError raised correctly)")
    else:
        print(f"FAILED (Unexpected RuntimeError: {e})")
        sys.exit(1)
except Exception as e:
    print(f"FAILED (Unexpected exception type: {type(e).__name__}: {e})")
    sys.exit(1)

# Test Case 3: Invalid JWT_ALGORITHM
print("Test Case 3: Invalid JWT_ALGORITHM startup failure...", end=" ")
force_cleanup_auth_utils()
os.getenv = make_mock_getenv("a" * 32, "RS256")
try:
    import auth_utils
    print("FAILED (no exception raised)")
    sys.exit(1)
except RuntimeError as e:
    if "Unsupported JWT_ALGORITHM: 'RS256'" in str(e):
        print("PASSED (RuntimeError raised correctly)")
    else:
        print(f"FAILED (Unexpected RuntimeError: {e})")
        sys.exit(1)
except Exception as e:
    print(f"FAILED (Unexpected exception type: {type(e).__name__}: {e})")
    sys.exit(1)

# Test Case 4: Non-integer JWT_EXPIRE_MINUTES
print("Test Case 4: Non-integer JWT_EXPIRE_MINUTES startup failure...", end=" ")
force_cleanup_auth_utils()
os.getenv = make_mock_getenv("a" * 32, "HS256", "not-an-integer")
try:
    import auth_utils
    print("FAILED (no exception raised)")
    sys.exit(1)
except RuntimeError as e:
    if "JWT_EXPIRE_MINUTES must be a valid integer" in str(e):
        print("PASSED (RuntimeError raised correctly)")
    else:
        print(f"FAILED (Unexpected RuntimeError: {e})")
        sys.exit(1)
except Exception as e:
    print(f"FAILED (Unexpected exception type: {type(e).__name__}: {e})")
    sys.exit(1)

# Test Case 5: JWT_EXPIRE_MINUTES = 0
print("Test Case 5: JWT_EXPIRE_MINUTES=0 startup failure...", end=" ")
force_cleanup_auth_utils()
os.getenv = make_mock_getenv("a" * 32, "HS256", "0")
try:
    import auth_utils
    print("FAILED (no exception raised)")
    sys.exit(1)
except RuntimeError as e:
    if "JWT_EXPIRE_MINUTES must be greater than zero" in str(e):
        print("PASSED (RuntimeError raised correctly)")
    else:
        print(f"FAILED (Unexpected RuntimeError: {e})")
        sys.exit(1)
except Exception as e:
    print(f"FAILED (Unexpected exception type: {type(e).__name__}: {e})")
    sys.exit(1)

# Test Case 6: JWT_EXPIRE_MINUTES < 0
print("Test Case 6: JWT_EXPIRE_MINUTES < 0 startup failure...", end=" ")
force_cleanup_auth_utils()
os.getenv = make_mock_getenv("a" * 32, "HS256", "-120")
try:
    import auth_utils
    print("FAILED (no exception raised)")
    sys.exit(1)
except RuntimeError as e:
    if "JWT_EXPIRE_MINUTES must be greater than zero" in str(e):
        print("PASSED (RuntimeError raised correctly)")
    else:
        print(f"FAILED (Unexpected RuntimeError: {e})")
        sys.exit(1)
except Exception as e:
    print(f"FAILED (Unexpected exception type: {type(e).__name__}: {e})")
    sys.exit(1)

# Test Case 7: Valid configuration starts successfully
print("Test Case 7: Valid configuration starts successfully...", end=" ")
force_cleanup_auth_utils()
os.getenv = make_mock_getenv("a" * 32, "HS256", "480")
try:
    import auth_utils
    print("PASSED")
except Exception as e:
    print(f"FAILED (Unexpected exception: {e})")
    sys.exit(1)

# Restore original environments and functions
os.getenv = original_getenv
if original_secret:
    os.environ["JWT_SECRET"] = original_secret
if original_algorithm:
    os.environ["JWT_ALGORITHM"] = original_algorithm
if original_expire:
    os.environ["JWT_EXPIRE_MINUTES"] = original_expire

print("\nALL PROGRAMMATIC STARTUP HARDENING TESTS PASSED SUCCESSFULLY!")
sys.exit(0)
