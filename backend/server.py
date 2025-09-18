<file>
<absolute_file_name>/app/backend/server.py</absolute_file_name>
<content_replace>
<old>            def periodicity(cd: Dict) -> str:
                wash = sweep = full = first = 0
                for key in ['september_1','september_2']:
                    b = cd.get(key) or {}
                    t = str(b.get('type') or '').lower()
                    dates = b.get('dates') or []
                    if not isinstance(dates, list):
                        dates = []
                    has_wash = ('влажная уборка' in t) or ('мытье' in t)
                    has_sweep = ('подмет' in t)
                    is_full = ('всех этаж' in t)
                    is_first = ('1 этажа' in t) or ('1 этаж' in t) or ('первые этаж' in t)
                    if has_wash: wash += len(dates)
                    if has_sweep: sweep += len(dates)
                    if has_wash and is_full: full += len(dates)
                    if has_wash and is_first: first += len(dates)
                if wash == 2 and sweep == 0: return '2 раза'
                if full >= 1 and first >= 1 and wash == (full + first) and sweep == 0: return '2 раза + первые этажи'
                if wash == 2 and sweep == 2: return 'Мытье 2 раза + подметание 2 раза'
                if wash >= 4: return '4 раза'
                return 'индивидуальная'</old>
<new>            def periodicity(cd: Dict) -> str:
                # Новая логика: считаем только полную влажную уборку как "раз"
                # Влажная уборка 1 этажа НЕ добавляет к количеству "раз"; она идёт вместе с подметанием
                full_wash = 0
                sweep = 0
                for key in ['september_1','september_2']:
                    b = cd.get(key) or {}
                    t = str(b.get('type') or '').lower()
                    dates = b.get('dates') or []
                    if not isinstance(dates, list):
                        dates = []
                    if 'всех этаж' in t and 'влажная уборка' in t:
                        full_wash += len(dates)
                    if 'подмет' in t:
                        sweep += len(dates)
                # Формирование метки
                if full_wash == 2 and sweep == 2:
                    return '2 раза + 2 подметания'
                if full_wash == 2 and sweep == 0:
                    return '2 раза'
                if full_wash >= 4:
                    return '4 раза'
                if full_wash == 1 and sweep >= 1:
                    return '1 раз + подметание'
                return 'индивидуальная'</new>
</content_replace>
</file>