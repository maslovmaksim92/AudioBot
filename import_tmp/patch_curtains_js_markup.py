#!/usr/bin/env python3
import time, shutil

P = "/opt/audiobot/frontend/src/components/Curtains/Curtains.js"
shutil.copy(P, P + ".bak_markup_" + str(int(time.time())))
src = open(P, encoding="utf-8").read()

# 1) хелперы после объявления rolledSection
old = "const rolledSection = product === 'зебра' ? prices?.zebra : prices?.rolled;"
new = """const rolledSection = product === 'зебра' ? prices?.zebra : prices?.rolled;
  const secMk = (sec) => (sec?.markup || prices?.markup || 1);
  const scaled = (data, m) =>
    Object.fromEntries(Object.entries(data || {}).map(([k, v]) => [k, Math.round(v * m)]));
  const rolledMk = secMk(rolledSection);"""
assert old in src
src = src.replace(old, new)

# 2) селект тканей рулонных/зебры — цены с наценкой
old = """              {Object.entries({ ...(rolledSection?.fabrics_per_m || {}), ...(rolledSection?.econom_fabrics_per_m || {}) }).map(([k, v]) => (
                <option key={k} value={k}>{k} ({fmt(v)} ₽/п.м)</option>
              ))}"""
new = """              {Object.entries(scaled({ ...(rolledSection?.fabrics_per_m || {}), ...(rolledSection?.econom_fabrics_per_m || {}) }, rolledMk)).map(([k, v]) => (
                <option key={k} value={k}>{k} ({fmt(v)} ₽/п.м)</option>
              ))}"""
assert old in src
src = src.replace(old, new)

# 3) селект систем — цены с наценкой
old = """              {Object.entries(rolledSection?.systems_per_m || {}).map(([k, v]) => (
                <option key={k} value={k}>{k} ({fmt(v)} ₽/п.м)</option>
              ))}"""
new = """              {Object.entries(scaled(rolledSection?.systems_per_m, rolledMk)).map(([k, v]) => (
                <option key={k} value={k}>{k} ({fmt(v)} ₽/п.м)</option>
              ))}"""
assert old in src
src = src.replace(old, new)

# 4) вкладка Прайс — таблицы рулонных/зебры с наценкой
old = """              <PriceTable title="Ткани (₽/пог.м)" data={{ ...(rolledSection?.fabrics_per_m || {}), ...(rolledSection?.econom_fabrics_per_m || {}) }} unit="₽" />
              <div className="space-y-4">
                <PriceTable title="Системы (₽/пог.м)" data={rolledSection?.systems_per_m} unit="₽" />"""
new = """              <PriceTable title="Ткани (₽/пог.м)" data={scaled({ ...(rolledSection?.fabrics_per_m || {}), ...(rolledSection?.econom_fabrics_per_m || {}) }, rolledMk)} unit="₽" />
              <div className="space-y-4">
                <PriceTable title="Системы (₽/пог.м)" data={scaled(rolledSection?.systems_per_m, rolledMk)} unit="₽" />"""
assert old in src
src = src.replace(old, new)

open(P, "w", encoding="utf-8").write(src)
print("Curtains.js PATCHED")
