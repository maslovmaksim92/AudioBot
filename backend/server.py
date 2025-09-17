<file>
<absolute_file_name>/app/backend/server.py</absolute_file_name>
<content_replace>
<old>app.include_router(api_router)</old>
<new>from .ai_training import router as ai_training_router

app.include_router(api_router)
app.include_router(ai_training_router)
</new>
</content_replace>
</file>