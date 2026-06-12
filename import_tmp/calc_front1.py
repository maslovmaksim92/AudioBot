p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

# 1) добавить иконку Calculator в импорт lucide
s = s.replace(
    "import { Building2, RefreshCw, CalendarDays, List, TrendingUp, Truck, FileCheck, Search, X } from 'lucide-react';",
    "import { Building2, RefreshCw, CalendarDays, List, TrendingUp, Truck, FileCheck, Search, X, Calculator } from 'lucide-react';"
)

# 2) состояние расчётов + загрузка — добавим после объявления notification
anchor_state = "  const [notification, setNotification] = useState(null);"
new_state = """  const [notification, setNotification] = useState(null);
  const [calcMonth, setCalcMonth] = useState(() => { const n = new Date(); return `${n.getFullYear()}-${String(n.getMonth()+1).padStart(2,'0')}`; });
  const [calcData, setCalcData] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);"""
assert anchor_state in s
s = s.replace(anchor_state, new_state, 1)

# 3) загрузка расчётов при открытии вкладки/смене месяца — добавим useEffect после существующих
anchor_eff = "  useEffect(() => { fetchHouses(); }, [activeFilters, pagination.page, pagination.limit]);"
new_eff = """  useEffect(() => { fetchHouses(); }, [activeFilters, pagination.page, pagination.limit]);
  useEffect(() => { if (activeTab === 'calc') fetchCalc(); }, [activeTab, calcMonth]);"""
assert anchor_eff in s
s = s.replace(anchor_eff, new_eff, 1)

# 4) функция fetchCalc — добавим перед "const handlePageChange"
anchor_fn = "  const handlePageChange = (newPage) =>"
new_fn = """  const fetchCalc = async () => {
    setCalcLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/api/cleaning/brigade-calc?month=${calcMonth}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setCalcData(await r.json());
    } catch (e) {
      console.error('calc error', e);
      setCalcData(null);
      showNotification('Ошибка загрузки расчётов', 'error');
    } finally {
      setCalcLoading(false);
    }
  };

  const handlePageChange = (newPage) =>"""
assert anchor_fn in s
s = s.replace(anchor_fn, new_fn, 1)

# 5) добавить вкладку 'calc' в навигацию
s = s.replace(
    "            { id: 'acts', label: 'Акты', Icon: FileCheck },",
    "            { id: 'acts', label: 'Акты', Icon: FileCheck },\n            { id: 'calc', label: 'Расчёты', Icon: Calculator },"
)

open(p, 'w', encoding='utf-8').write(s)
print("OK: состояние, загрузка и вкладка 'Расчёты' добавлены")
