#!/usr/bin/env python3
"""
Анализ выписок ООО ВАШ ДОМ
"""
import pandas as pd
import re

files = [
    '/tmp/vyp1.xlsx',
]

for file in files:
    print(f"\n{'='*60}")
    print(f"Файл: {file}")
    print('='*60)
    
    # Читаем со строки 8 (заголовки)
    df = pd.read_excel(file, header=8)
    
    print(f"\nКолонки: {df.columns.tolist()}")
    print(f"\nКоличество строк: {len(df)}")
    
    # Ищем колонки с нужными данными
    print("\n=== ПЕРВЫЕ 10 СТРОК ===")
    print(df.head(10))
    
    # Ищем поступления (кредитовые операции)
    print("\n=== АНАЛИЗ ДАННЫХ ===")
    for col in df.columns:
        if pd.notna(col) and 'сумма' in str(col).lower():
            print(f"Колонка с суммой: {col}")
        if pd.notna(col) and ('дата' in str(col).lower() or 'период' in str(col).lower()):
            print(f"Колонка с датой: {col}")
        if pd.notna(col) and ('назнач' in str(col).lower() or 'основан' in str(col).lower()):
            print(f"Колонка с назначением: {col}")
        if pd.notna(col) and ('плател' in str(col).lower() or 'контраг' in str(col).lower()):
            print(f"Колонка с плательщиком: {col}")
