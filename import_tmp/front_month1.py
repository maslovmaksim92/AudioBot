p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

# 1) состояние месяца списка (по умолчанию текущий) — добавим в useState блок activeFilters
OLD_ST = """  const [activeFilters, setActiveFilters] = useState({
    brigade: '', management_company: '', search: '', periodicity: '',
    cleaning_date: '', date_from: '', date_to: '',
  });"""
NEW_ST = """  const [listMonth, setListMonth] = useState(() => {
    const n = new Date(); return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}`;
  });
  const [activeFilters, setActiveFilters] = useState({
    brigade: '', management_company: '', search: '', periodicity: '',
    cleaning_date: '', date_from: '', date_to: '',
  });"""
assert OLD_ST in s
s = s.replace(OLD_ST, NEW_ST)

# 2) перезагрузка при смене месяца
OLD_EFF = "  useEffect(() => { fetchHouses(); }, [activeFilters, pagination.page, pagination.limit]);"
NEW_EFF = "  useEffect(() => { fetchHouses(); }, [activeFilters, pagination.page, pagination.limit, listMonth]);"
assert OLD_EFF in s
s = s.replace(OLD_EFF, NEW_EFF)

# 3) передать month в запрос
OLD_Q = """      q.append('page', String(pagination.page));
      q.append('limit', String(pagination.limit));"""
NEW_Q = """      if (listMonth) q.append('month', listMonth);
      q.append('page', String(pagination.page));
      q.append('limit', String(pagination.limit));"""
assert OLD_Q in s
s = s.replace(OLD_Q, NEW_Q)

# 4) периодичность: клиентский фильтр по подстроке (значения стали текстовыми)
OLD_VIS = """  // клиентский фильтр по периодичности (бэкенд её вычисляет, но не фильтрует)
  const visibleHouses = activeFilters.periodicity
    ? houses.filter(h => (h.periodicity || '') === activeFilters.periodicity)
    : houses;

  const periodicityOptions = ['1 раз в месяц', '2 раза в месяц', '3 раза в месяц', '4 раза в месяц', 'не указана'];"""
NEW_VIS = """  // клиентский фильтр по периодичности (подстрока, т.к. формулировки разные)
  const visibleHouses = activeFilters.periodicity
    ? houses.filter(h => (h.periodicity || '').toLowerCase().includes(activeFilters.periodicity.toLowerCase()))
    : houses;

  const periodicityOptions = ['2 мытья', '4 мытья', 'подметания', '1 этажа', 'индивидуальный'];"""
assert OLD_VIS in s
s = s.replace(OLD_VIS, NEW_VIS)

open(p, 'w', encoding='utf-8').write(s)
print("OK: состояние месяца, запрос month, фильтр периодичности обновлены")
