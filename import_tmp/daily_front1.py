p = '/opt/audiobot/frontend/src/components/Works/Works.js'
s = open(p, encoding='utf-8').read()

# иконку CalendarRange в импорт
s = s.replace(
    "import { Building2, RefreshCw, CalendarDays, List, TrendingUp, Truck, FileCheck, Search, X, Calculator } from 'lucide-react';",
    "import { Building2, RefreshCw, CalendarDays, List, TrendingUp, Truck, FileCheck, Search, X, Calculator, CalendarRange } from 'lucide-react';"
)

# состояние daily
anchor_state = "  const [calcLoading, setCalcLoading] = useState(false);"
new_state = """  const [calcLoading, setCalcLoading] = useState(false);
  const [dailyData, setDailyData] = useState(null);
  const [dailyLoading, setDailyLoading] = useState(false);
  const [expandedDay, setExpandedDay] = useState(null);"""
assert anchor_state in s
s = s.replace(anchor_state, new_state, 1)

# загрузка daily при открытии вкладки/смене месяца (reuse calcMonth)
anchor_eff = "  useEffect(() => { if (activeTab === 'calc') fetchCalc(); }, [activeTab, calcMonth]);"
new_eff = """  useEffect(() => { if (activeTab === 'calc') fetchCalc(); }, [activeTab, calcMonth]);
  useEffect(() => { if (activeTab === 'daily') fetchDaily(); }, [activeTab, calcMonth]);"""
assert anchor_eff in s
s = s.replace(anchor_eff, new_eff, 1)

# функция fetchDaily перед fetchCalc
anchor_fn = "  const fetchCalc = async () => {"
new_fn = """  const fetchDaily = async () => {
    setDailyLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/api/cleaning/daily-calc?month=${calcMonth}`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      setDailyData(await r.json());
    } catch (e) {
      console.error('daily error', e);
      setDailyData(null);
      showNotification('Ошибка загрузки расчётов по дням', 'error');
    } finally {
      setDailyLoading(false);
    }
  };

  const fetchCalc = async () => {"""
assert anchor_fn in s
s = s.replace(anchor_fn, new_fn, 1)

# вкладка в навигацию
s = s.replace(
    "            { id: 'calc', label: 'Расчёты', Icon: Calculator },",
    "            { id: 'calc', label: 'Расчёты', Icon: Calculator },\n            { id: 'daily', label: 'Расчёты по дням', Icon: CalendarRange },"
)

open(p, 'w', encoding='utf-8').write(s)
print("OK: состояние/загрузка/вкладка 'Расчёты по дням' добавлены")
