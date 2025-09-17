<file>
<absolute_file_name>/app/frontend/src/components/Training/Training.js</absolute_file_name>
<content_replace>
<old>        <div className="flex flex-col gap-3 md:flex-row md:items-center md:gap-4">
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.xlsx,.zip"
            onChange={handleFileChange}
            className="block text-sm"
          />
          <button
            onClick={handleUpload}
            disabled={!canUpload}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50"
          >
            {uploading ? 'Загрузка...' : 'Анализировать'}
          </button>
          {files.length > 0 && (
            <span className="text-xs text-gray-600">
              Выбрано: {files.length} • Общий размер: {fmtBytes(files.reduce((a,f)=>a+(f.size||0),0))}
            </span>
          )}
        </div>
</old>
<new>        <div className="flex flex-col gap-3 md:flex-row md:items-center md:gap-4">
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.xlsx,.zip"
            onChange={handleFileChange}
            className="block text-sm"
          />
          <div className="flex gap-2 items-center">
            <label className="text-xs text-gray-600">Chunk tokens</label>
            <input type="number" className="w-24 px-2 py-1 rounded border border-gray-300" value={chunkTokens} min={300} max={3000} onChange={(e)=>setChunkTokens(Number(e.target.value)||1200)} />
            <label className="text-xs text-gray-600">Overlap</label>
            <input type="number" className="w-20 px-2 py-1 rounded border border-gray-300" value={overlap} min={0} max={500} onChange={(e)=>setOverlap(Number(e.target.value)||200)} />
          </div>
          <button
            onClick={handleUpload}
            disabled={!canUpload}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50"
          >
            {uploading ? 'Загрузка...' : 'Анализировать'}
          </button>
          {files.length > 0 && (
            <span className="text-xs text-gray-600">
              Выбрано: {files.length} • Общий размер: {fmtBytes(files.reduce((a,f)=>a+(f.size||0),0))}
            </span>
          )}
        </div>
</new>
</content_replace>
</file>