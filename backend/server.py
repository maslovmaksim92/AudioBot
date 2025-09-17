<file>
<absolute_file_name>/app/backend/server.py</absolute_file_name>
<content_replace>
<old>    rows = (await db.execute(sa_text('SELECT id, filename, mime, size_bytes, summary, created_at, pages FROM ai_documents ORDER BY created_at DESC LIMIT 200'))).all()</old>
<new>    rows = (await db.execute(sa_text('''
        SELECT d.id, d.filename, d.mime, d.size_bytes, d.summary, d.created_at, d.pages,
               (SELECT COUNT(1) FROM ai_chunks c WHERE c.document_id=d.id) AS chunks_count
        FROM ai_documents d
        ORDER BY d.created_at DESC
        LIMIT 200
    '''))).all()</new>
</content_replace>
</file>