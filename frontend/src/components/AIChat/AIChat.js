<file>
<absolute_file_name>/app/frontend/src/components/AIChat/AIChat.js</absolute_file_name>
<content_replace>
<old>  return (
    <div className="p-8 max-w-4xl mx-auto h-screen flex flex-col">
</old>
<new>  useEffect(()=>()=>{ try { wsRef.current?.close(); } catch {} },[]);

  return (
    <div className="p-8 max-w-4xl mx-auto h-screen flex flex-col">
</new>
</content_replace>
</file>