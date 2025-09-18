<file>
<absolute_file_name>/app/backend/server.py</absolute_file_name>
<content_replace>
<old># Mount routers
app.include_router(api_router)

# Import and mount AI Training router (isolated)
try:
    from .ai_training import router as ai_training_router  # backend is a package
    app.include_router(ai_training_router)
except Exception:
    # If relative import fails in some environments, try absolute import
    try:
        from ai_training import router as ai_training_router  # type: ignore
        app.include_router(ai_training_router)
    except Exception as e:
        logger.warning(f"AI Training router not mounted: {e}")
</old>
<new># Mount routers
app.include_router(api_router)

# Import and mount AI Training router (isolated)
try:
    from .ai_training import router as ai_training_router  # backend is a package
    app.include_router(ai_training_router)
except Exception:
    # If relative import fails in some environments, try absolute import
    try:
        from ai_training import router as ai_training_router  # type: ignore
        app.include_router(ai_training_router)
    except Exception as e:
        logger.warning(f"AI Training router not mounted: {e}")

# Import and mount Voice router
try:
    from .voice import router as voice_router
    app.include_router(voice_router)
except Exception:
    try:
        from voice import router as voice_router  # type: ignore
        app.include_router(voice_router)
    except Exception as e:
        logger.warning(f"Voice router not mounted: {e}")
</new>
</content_replace>
</file>