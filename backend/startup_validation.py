import os
import logging
from pathlib import Path
from database import engine

logger = logging.getLogger("startup_validation")

def validate_startup_environment():
    logger.info("=== STARTING PRE-RELEASE STARTUP ENVIRONMENT VALIDATION ===")
    
    # Get APP_ENV (default to development)
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    logger.info(f"Environment Mode: {APP_ENV.upper()}")

    WEAK_PLACEHOLDERS = ["changeme", "password", "secret123", "test"]

    def check_weak_secret(secret_name, secret_value):
        if secret_value and APP_ENV == "production":
            val_lower = secret_value.lower()
            if any(p in val_lower for p in WEAK_PLACEHOLDERS):
                raise RuntimeError(f"FATAL: Production secret '{secret_name}' contains a weak placeholder value. Application cannot start.")

    # 1. Validate DATABASE_URL connectivity
    db_url = os.getenv("DATABASE_URL")
    if not db_url or not db_url.strip():
        raise RuntimeError("DATABASE_URL environment variable is missing or empty. Application cannot start.")
    
    check_weak_secret("DATABASE_URL", db_url)

    is_postgres = "postgresql" in db_url or "postgres" in db_url
    if is_postgres:
        logger.info("Database Mode: PostgreSQL/Supabase")
    elif "sqlite" in db_url:
        logger.info("Database Mode: SQLite")
    else:
        logger.warning(f"Database Mode: Unknown dialect in URL: {db_url}")

    # Connect to check connectivity
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1")).fetchone()
            logger.info("Database connectivity test: PASSED")
    except Exception as e:
        if APP_ENV == "production" or is_postgres:
            raise RuntimeError(
                f"Database validation failed: Unable to connect to production database. Error: {e}\n"
                f"Remediation: Confirm PostgreSQL/Supabase database status or check network routes."
            )
        else:
            logger.warning(f"Local database connectivity warning (non-fatal in development/SQLite): {e}")

    # 2. Validate JWT_SECRET strength and existence
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret or not jwt_secret.strip():
        msg = "JWT_SECRET environment variable is missing or empty."
        if APP_ENV == "production":
            raise RuntimeError("FATAL: " + msg)
        else:
            logger.warning("WARNING: " + msg)
    elif len(jwt_secret) < 32:
        msg = "JWT_SECRET is too weak. It must be at least 32 characters long."
        if APP_ENV == "production":
            raise RuntimeError("FATAL: " + msg)
        else:
            logger.warning("WARNING: " + msg)
    else:
        check_weak_secret("JWT_SECRET", jwt_secret)
        logger.info("JWT_SECRET validation: PASSED")

    # 3. Validate GROQ_API_KEY existence
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key or not groq_api_key.strip():
        msg = "GROQ_API_KEY environment variable is missing or empty. Groq LLM integration will fail."
        if APP_ENV == "production":
            raise RuntimeError("FATAL: " + msg)
        else:
            logger.warning("WARNING: " + msg)
    else:
        check_weak_secret("GROQ_API_KEY", groq_api_key)
        logger.info("GROQ_API_KEY validation: PASSED")

    # 4. Validate SentenceTransformer model availability
    try:
        from embeddings import model, RAG_ENABLED
        if RAG_ENABLED and model is None:
            raise RuntimeError("SentenceTransformer model is not loaded correctly.")
        
        if not RAG_ENABLED:
            logger.warning("WARNING: Embedding model unavailable. RAG disabled.")
            if APP_ENV == "production":
                raise RuntimeError("FATAL: SentenceTransformer model failed to load. Startup aborted in production mode.")
        else:
            logger.info("SentenceTransformer model availability: PASSED")
    except Exception as e:
        if APP_ENV == "production":
            raise RuntimeError(f"SentenceTransformer validation failed in production: {e}")
        else:
            logger.warning(f"SentenceTransformer load warning: {e}. RAG features disabled.")

    # 5. Validate FAISS index initialization & load success
    try:
        import report_vector_store as rvs
        if rvs._index is None:
            raise RuntimeError("FAISS index is not initialized.")
        logger.info("FAISS index initialization: PASSED")
    except Exception as e:
        if APP_ENV == "production":
            raise RuntimeError(f"FAISS index validation failed in production: {e}")
        else:
            logger.warning(f"FAISS index warning: {e}")

    # 6. Validate vector metadata load success
    try:
        metadata_file = rvs._metadata_path()
        if metadata_file.is_file():
            with open(metadata_file, "r", encoding="utf-8") as f:
                import json
                json.load(f)
            logger.info("Vector metadata file load and JSON parsing: PASSED")
        else:
            logger.info("Vector metadata file does not exist yet (will be created on first upload): PASSED")
    except Exception as e:
        if APP_ENV == "production":
            raise RuntimeError(f"Vector metadata load verification failed in production: {e}")
        else:
            logger.warning(f"Vector metadata warning: {e}")

    # 7. Validate embedding dimension == FAISS index dimension
    try:
        from embeddings import generate_embedding, RAG_ENABLED
        if RAG_ENABLED:
            test_emb = generate_embedding("validation")
            emb_dim = len(test_emb)
            index_dim = rvs._index.d
            if emb_dim != index_dim:
                raise RuntimeError(f"Embedding dimension ({emb_dim}) does not match FAISS index dimension ({index_dim}).")
            logger.info(f"Embedding dimension consistency validation: PASSED (dimension = {emb_dim})")
        else:
            logger.warning("RAG disabled, skipping dimension consistency check.")
    except Exception as e:
        if APP_ENV == "production":
            raise RuntimeError(f"Dimension verification failed: {e}")
        else:
            logger.warning(f"Dimension verification warning: {e}")

    # 8. Validate uploads directory structure
    backend_dir = Path(__file__).resolve().parent
    required_dirs = [
        backend_dir / "uploads",
        backend_dir / "uploads" / "reports"
    ]
    for d in required_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = d / ".startup_write_test"
            test_file.write_text("write test")
            test_file.unlink()
            logger.info(f"Directory structure validated: {d.relative_to(backend_dir)} (exists and writable)")
        except Exception as e:
            raise RuntimeError(f"Directory write validation failed for {d}: {e}")

    logger.info("=== PRE-RELEASE STARTUP ENVIRONMENT VALIDATION PASSED SUCCESSFULLY ===")
