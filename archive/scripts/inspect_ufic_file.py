#!/usr/bin/env python3
"""
Инспектирование файла УФИЦ
"""
import pandas as pd

# Читаем Excel файл
df = pd.read_excel('/tmp/ufic.xlsx', header=None)

print("=== СТРУКТУРА ФАЙЛА ===")
print(f"Размер: {df.shape[0]} строк x {df.shape[1]} колонок")
print("\n=== ПЕРВЫЕ 30 СТРОК ===")
print(df.head(30))
print("\n=== ИНФОРМАЦИЯ О КОЛОНКАХ ===")
print(df.info())
