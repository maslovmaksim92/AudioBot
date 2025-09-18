<file>
<absolute_file_name>/app/frontend/src/components/Works/Works.js</absolute_file_name>
<content_replace>
<old>        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-2">
          <select
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            value={activeFilters.brigade}
            onChange={(e) => { setActiveFilters(prev => ({ ...prev, brigade: e.target.value })); setPagination(prev => ({...prev, page: 1})); }}
          >
            <option value="">Все бригады</option>
            {filters.brigades?.map((brigade, index) => (
              <option key={index} value={brigade}>{brigade}</option>
            ))}
          </select>

          <select
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            value={activeFilters.management_company}
            onChange={(e) => { setActiveFilters(prev => ({ ...prev, management_company: e.target.value })); setPagination(prev => ({...prev, page: 1})); }}
          >
            <option value="">Все УК</option>
            {filters.management_companies?.map((company, index) => (
              <option key={index} value={company}>{company}</option>
            ))}
          </select>

          {/* Фильтр по дате уборки */}
          <DatePicker
            selected={activeFilters.cleaning_date ? new Date(activeFilters.cleaning_date) : null}
            onChange={(date) => {
              const val = date ? format(date, 'yyyy-MM-dd') : '';
              setActiveFilters(prev => ({ ...prev, cleaning_date: val }));
              setPagination(prev => ({...prev, page: 1}));
              window.scrollTo({top: 0, behavior: 'smooth'});
            }}
            placeholderText="Дата уборки"
            dateFormat="yyyy-MM-dd"
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            locale={ru}
            isClearable
          />



        </div></old>
<new>        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-2">
          <input
            type="text"
            placeholder="Адрес / название дома"
            value={activeFilters.search}
            onChange={(e)=>{ setActiveFilters(prev=>({...prev, search: e.target.value})); setPagination(prev=>({...prev, page:1})); }}
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
          />

          <select
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            value={activeFilters.brigade}
            onChange={(e) => { setActiveFilters(prev => ({ ...prev, brigade: e.target.value })); setPagination(prev => ({...prev, page: 1})); }}
          >
            <option value="">Все бригады</option>
            {filters.brigades?.map((brigade, index) => (
              <option key={index} value={brigade}>{brigade}</option>
            ))}
          </select>

          <select
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            value={activeFilters.management_company}
            onChange={(e) => { setActiveFilters(prev => ({ ...prev, management_company: e.target.value })); setPagination(prev => ({...prev, page: 1})); }}
          >
            <option value="">Все УК</option>
            {filters.management_companies?.map((company, index) => (
              <option key={index} value={company}>{company}</option>
            ))}
          </select>

          {/* Фильтр по дате уборки */}
          <DatePicker
            selected={activeFilters.cleaning_date ? new Date(activeFilters.cleaning_date) : null}
            onChange={(date) => {
              const val = date ? format(date, 'yyyy-MM-dd') : '';
              setActiveFilters(prev => ({ ...prev, cleaning_date: val }));
              setPagination(prev => ({...prev, page: 1}));
              window.scrollTo({top: 0, behavior: 'smooth'});
            }}
            placeholderText="Дата уборки"
            dateFormat="yyyy-MM-dd"
            className="w-full p-3 border border-gray-300 rounded-lg bg-white"
            locale={ru}
            isClearable
          />
        </div>

        <div className="flex items-center gap-3 mb-3">
          <span className="text-sm text-gray-500">Показывать:</span>
          {[50,100,200,500,1000].map(n => (
            <button key={n} onClick={()=>handleLimitChange(n)} className={`px-2 py-1 text-xs rounded-md ${pagination.limit===n? 'bg-blue-600 text-white':'bg-gray-100 hover:bg-gray-200 text-gray-700'}`}>{n}</button>
          ))}
        </div></new>
</content_replace>
</file>