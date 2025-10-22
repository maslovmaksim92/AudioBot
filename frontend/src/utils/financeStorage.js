// Централизованное хранилище финансовых данных
const STORAGE_KEYS = {
  TRANSACTIONS: 'vasdom_transactions',
  DEBTS: 'vasdom_debts',
  INVENTORY: 'vasdom_inventory',
  REVENUE: 'vasdom_revenue',
  EXPENSES: 'vasdom_expenses',
  BUDGETS: 'vasdom_budgets',
  PAYMENT_CALENDAR: 'vasdom_payment_calendar'
};

// НДС ставки
export const VAT_RATES = {
  NONE: 0,
  VAT_10: 10,
  VAT_20: 20
};

// Расчет НДС
export const calculateVAT = (amount, rate) => {
  return amount * (rate / 100);
};

export const calculateAmountWithVAT = (amount, rate) => {
  return amount * (1 + rate / 100);
};

export const extractVATFromAmount = (amountWithVAT, rate) => {
  return amountWithVAT * (rate / (100 + rate));
};

export const getAmountWithoutVAT = (amountWithVAT, rate) => {
  return amountWithVAT / (1 + rate / 100);
};

// Инициализация данных
const initData = () => {
  const transactions = localStorage.getItem(STORAGE_KEYS.TRANSACTIONS);
  if (!transactions) {
    localStorage.setItem(STORAGE_KEYS.TRANSACTIONS, JSON.stringify([]));
  }
  
  const debts = localStorage.getItem(STORAGE_KEYS.DEBTS);
  if (!debts) {
    localStorage.setItem(STORAGE_KEYS.DEBTS, JSON.stringify([]));
  }
  
  const inventory = localStorage.getItem(STORAGE_KEYS.INVENTORY);
  if (!inventory) {
    localStorage.setItem(STORAGE_KEYS.INVENTORY, JSON.stringify([]));
  }
  
  const revenue = localStorage.getItem(STORAGE_KEYS.REVENUE);
  if (!revenue) {
    localStorage.setItem(STORAGE_KEYS.REVENUE, JSON.stringify([]));
  }
  
  const expenses = localStorage.getItem(STORAGE_KEYS.EXPENSES);
  if (!expenses) {
    localStorage.setItem(STORAGE_KEYS.EXPENSES, JSON.stringify([]));
  }
};

// Транзакции
export const getTransactions = () => {
  initData();
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.TRANSACTIONS) || '[]');
};

export const addTransaction = (transaction) => {
  const transactions = getTransactions();
  
  // Рассчитываем НДС если указана ставка
  const vatRate = transaction.vat_rate || 0;
  const amountWithoutVAT = transaction.amount;
  const vatAmount = calculateVAT(amountWithoutVAT, vatRate);
  const totalAmount = amountWithoutVAT + vatAmount;
  
  const newTransaction = {
    id: `trans-${Date.now()}`,
    ...transaction,
    amount: parseFloat(amountWithoutVAT),
    vat_rate: vatRate,
    vat_amount: vatAmount,
    total_amount: totalAmount,
    created_at: new Date().toISOString()
  };
  
  transactions.push(newTransaction);
  localStorage.setItem(STORAGE_KEYS.TRANSACTIONS, JSON.stringify(transactions));
  return newTransaction;
};

export const updateTransaction = (id, updates) => {
  const transactions = getTransactions();
  const index = transactions.findIndex(t => t.id === id);
  if (index !== -1) {
    transactions[index] = { ...transactions[index], ...updates, updated_at: new Date().toISOString() };
    localStorage.setItem(STORAGE_KEYS.TRANSACTIONS, JSON.stringify(transactions));
    return transactions[index];
  }
  return null;
};

export const deleteTransaction = (id) => {
  const transactions = getTransactions();
  const filtered = transactions.filter(t => t.id !== id);
  localStorage.setItem(STORAGE_KEYS.TRANSACTIONS, JSON.stringify(filtered));
  return true;
};

// Задолженности
export const getDebts = () => {
  initData();
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.DEBTS) || '[]');
};

export const addDebt = (debt) => {
  const debts = getDebts();
  const newDebt = {
    id: `debt-${Date.now()}`,
    ...debt,
    created_at: new Date().toISOString()
  };
  debts.push(newDebt);
  localStorage.setItem(STORAGE_KEYS.DEBTS, JSON.stringify(debts));
  return newDebt;
};

export const updateDebt = (id, updates) => {
  const debts = getDebts();
  const index = debts.findIndex(d => d.id === id);
  if (index !== -1) {
    debts[index] = { ...debts[index], ...updates, updated_at: new Date().toISOString() };
    localStorage.setItem(STORAGE_KEYS.DEBTS, JSON.stringify(debts));
    return debts[index];
  }
  return null;
};

export const deleteDebt = (id) => {
  const debts = getDebts();
  const filtered = debts.filter(d => d.id !== id);
  localStorage.setItem(STORAGE_KEYS.DEBTS, JSON.stringify(filtered));
  return true;
};

// Запасы
export const getInventory = () => {
  initData();
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.INVENTORY) || '[]');
};

export const addInventoryItem = (item) => {
  const inventory = getInventory();
  const newItem = {
    id: `inv-${Date.now()}`,
    ...item,
    value: item.quantity * item.cost,
    created_at: new Date().toISOString()
  };
  inventory.push(newItem);
  localStorage.setItem(STORAGE_KEYS.INVENTORY, JSON.stringify(inventory));
  return newItem;
};

export const updateInventoryItem = (id, updates) => {
  const inventory = getInventory();
  const index = inventory.findIndex(i => i.id === id);
  if (index !== -1) {
    const updated = { ...inventory[index], ...updates, updated_at: new Date().toISOString() };
    updated.value = updated.quantity * updated.cost;
    inventory[index] = updated;
    localStorage.setItem(STORAGE_KEYS.INVENTORY, JSON.stringify(inventory));
    return inventory[index];
  }
  return null;
};

export const deleteInventoryItem = (id) => {
  const inventory = getInventory();
  const filtered = inventory.filter(i => i.id !== id);
  localStorage.setItem(STORAGE_KEYS.INVENTORY, JSON.stringify(filtered));
  return true;
};

// Выручка
export const getRevenue = () => {
  initData();
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.REVENUE) || '[]');
};

export const setMonthlyRevenue = (month, amount, notes = '') => {
  const revenue = getRevenue();
  const existing = revenue.find(r => r.month === month);
  
  if (existing) {
    existing.amount = amount;
    existing.notes = notes;
    existing.updated_at = new Date().toISOString();
  } else {
    revenue.push({
      id: `rev-${Date.now()}`,
      month,
      amount,
      notes,
      created_at: new Date().toISOString()
    });
  }
  
  localStorage.setItem(STORAGE_KEYS.REVENUE, JSON.stringify(revenue));
  return revenue;
};

// Бюджеты (план)
export const getBudgets = () => {
  initData();
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.BUDGETS) || '[]');
};

export const addBudget = (budget) => {
  const budgets = getBudgets();
  const newBudget = {
    id: `budget-${Date.now()}`,
    ...budget,
    created_at: new Date().toISOString()
  };
  budgets.push(newBudget);
  localStorage.setItem(STORAGE_KEYS.BUDGETS, JSON.stringify(budgets));
  return newBudget;
};

export const updateBudget = (id, updates) => {
  const budgets = getBudgets();
  const index = budgets.findIndex(b => b.id === id);
  if (index !== -1) {
    budgets[index] = { ...budgets[index], ...updates, updated_at: new Date().toISOString() };
    localStorage.setItem(STORAGE_KEYS.BUDGETS, JSON.stringify(budgets));
    return budgets[index];
  }
  return null;
};

export const deleteBudget = (id) => {
  const budgets = getBudgets();
  const filtered = budgets.filter(b => b.id !== id);
  localStorage.setItem(STORAGE_KEYS.BUDGETS, JSON.stringify(filtered));
  return true;
};

// Платежный календарь (предстоящие платежи)
export const getPaymentCalendar = () => {
  initData();
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.PAYMENT_CALENDAR) || '[]');
};

export const addPaymentEvent = (payment) => {
  const calendar = getPaymentCalendar();
  const newPayment = {
    id: `payment-${Date.now()}`,
    ...payment,
    status: payment.status || 'planned', // planned, paid, cancelled
    created_at: new Date().toISOString()
  };
  calendar.push(newPayment);
  localStorage.setItem(STORAGE_KEYS.PAYMENT_CALENDAR, JSON.stringify(calendar));
  return newPayment;
};

export const updatePaymentEvent = (id, updates) => {
  const calendar = getPaymentCalendar();
  const index = calendar.findIndex(p => p.id === id);
  if (index !== -1) {
    calendar[index] = { ...calendar[index], ...updates, updated_at: new Date().toISOString() };
    localStorage.setItem(STORAGE_KEYS.PAYMENT_CALENDAR, JSON.stringify(calendar));
    return calendar[index];
  }
  return null;
};

export const deletePaymentEvent = (id) => {
  const calendar = getPaymentCalendar();
  const filtered = calendar.filter(p => p.id !== id);
  localStorage.setItem(STORAGE_KEYS.PAYMENT_CALENDAR, JSON.stringify(filtered));
  return true;
};

// План-факт анализ
export const getPlanFactAnalysis = (month) => {
  const budgets = getBudgets();
  const transactions = getTransactions();
  
  // Фильтруем бюджет и транзакции по месяцу
  const monthBudgets = budgets.filter(b => b.month === month);
  const monthTransactions = transactions.filter(t => {
    const date = new Date(t.date);
    const transMonth = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
    return transMonth === month;
  });
  
  // Группируем по категориям
  const analysis = {};
  
  // Добавляем плановые данные
  monthBudgets.forEach(b => {
    if (!analysis[b.category]) {
      analysis[b.category] = {
        category: b.category,
        type: b.type,
        plan: 0,
        fact: 0,
        variance: 0,
        variance_percent: 0
      };
    }
    analysis[b.category].plan += parseFloat(b.amount);
  });
  
  // Добавляем фактические данные
  monthTransactions.forEach(t => {
    if (!analysis[t.category]) {
      analysis[t.category] = {
        category: t.category,
        type: t.type,
        plan: 0,
        fact: 0,
        variance: 0,
        variance_percent: 0
      };
    }
    analysis[t.category].fact += parseFloat(t.total_amount || t.amount);
  });
  
  // Рассчитываем отклонения
  Object.keys(analysis).forEach(category => {
    const item = analysis[category];
    item.variance = item.fact - item.plan;
    item.variance_percent = item.plan !== 0 ? (item.variance / item.plan) * 100 : 0;
  });
  
  return Object.values(analysis);
};
  initData();
  return JSON.parse(localStorage.getItem(STORAGE_KEYS.EXPENSES) || '[]');
};

export const addExpense = (expense) => {
  const expenses = getExpenses();
  const newExpense = {
    id: `exp-${Date.now()}`,
    ...expense,
    created_at: new Date().toISOString()
  };
  expenses.push(newExpense);
  localStorage.setItem(STORAGE_KEYS.EXPENSES, JSON.stringify(expenses));
  return newExpense;
};

export const updateExpense = (id, updates) => {
  const expenses = getExpenses();
  const index = expenses.findIndex(e => e.id === id);
  if (index !== -1) {
    expenses[index] = { ...expenses[index], ...updates, updated_at: new Date().toISOString() };
    localStorage.setItem(STORAGE_KEYS.EXPENSES, JSON.stringify(expenses));
    return expenses[index];
  }
  return null;
};

export const deleteExpense = (id) => {
  const expenses = getExpenses();
  const filtered = expenses.filter(e => e.id !== id);
  localStorage.setItem(STORAGE_KEYS.EXPENSES, JSON.stringify(filtered));
  return true;
};

// Расчеты (правильные финансовые формулы)
export const calculateFinancialData = () => {
  const transactionsData = getTransactions();
  const debtsData = getDebts();
  const inventoryData = getInventory();
  const revenueData = getRevenue();
  const budgetsData = getBudgets();
  
  const transactions = Array.isArray(transactionsData) ? transactionsData : [];
  const debts = Array.isArray(debtsData) ? debtsData : [];
  const inventory = Array.isArray(inventoryData) ? inventoryData : [];
  const revenue = Array.isArray(revenueData) ? revenueData : [];
  const budgets = Array.isArray(budgetsData) ? budgetsData : [];
  
  // 1. ДВИЖЕНИЕ ДЕНЕЖНЫХ СРЕДСТВ (Cash Flow)
  const monthlyData = {};
  const dailyData = {};
  
  transactions.forEach(t => {
    try {
      const date = new Date(t.date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      const dayKey = date.toISOString().split('T')[0];
      
      if (!monthlyData[monthKey]) {
        monthlyData[monthKey] = { 
          income: 0, 
          expense: 0, 
          income_vat: 0, 
          expense_vat: 0,
          net_profit: 0 
        };
      }
      
      if (!dailyData[dayKey]) {
        dailyData[dayKey] = { 
          income: 0, 
          expense: 0, 
          balance: 0 
        };
      }
      
      const amount = parseFloat(t.total_amount || t.amount) || 0;
      const vatAmount = parseFloat(t.vat_amount) || 0;
      
      if (t.type === 'income') {
        monthlyData[monthKey].income += amount;
        monthlyData[monthKey].income_vat += vatAmount;
        dailyData[dayKey].income += amount;
      } else {
        monthlyData[monthKey].expense += amount;
        monthlyData[monthKey].expense_vat += vatAmount;
        dailyData[dayKey].expense += amount;
      }
    } catch (e) {
      console.error('Error processing transaction:', e);
    }
  });
  
  // Рассчитываем чистую прибыль по месяцам
  Object.keys(monthlyData).forEach(month => {
    const data = monthlyData[month];
    data.net_profit = data.income - data.expense;
    data.margin = data.income !== 0 ? ((data.net_profit / data.income) * 100).toFixed(2) : 0;
  });
  
  // Рассчитываем накопительный баланс по дням
  const sortedDays = Object.keys(dailyData).sort();
  let runningBalance = 0;
  sortedDays.forEach(day => {
    runningBalance += dailyData[day].income - dailyData[day].expense;
    dailyData[day].balance = runningBalance;
  });
  
  // Добавляем ручную выручку
  revenue.forEach(r => {
    try {
      const [monthName, year] = r.month.split(' ');
      const monthIndex = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                         'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'].indexOf(monthName);
      const monthKey = `${year}-${String(monthIndex + 1).padStart(2, '0')}`;
      
      if (!monthlyData[monthKey]) {
        monthlyData[monthKey] = { income: 0, expense: 0, income_vat: 0, expense_vat: 0, net_profit: 0 };
      }
      monthlyData[monthKey].income += parseFloat(r.amount) || 0;
      monthlyData[monthKey].net_profit = monthlyData[monthKey].income - monthlyData[monthKey].expense;
    } catch (e) {
      console.error('Error processing revenue:', e);
    }
  });
  
  // 2. ЗАДОЛЖЕННОСТИ (Debts)
  const totalDebts = debts
    .filter(d => d.status === 'active' || d.status === 'overdue')
    .reduce((sum, d) => sum + (parseFloat(d.amount) || 0), 0);
  const overdueDebts = debts
    .filter(d => d.status === 'overdue')
    .reduce((sum, d) => sum + (parseFloat(d.amount) || 0), 0);
  const activeDebts = totalDebts - overdueDebts;
  
  // 3. ТОВАРНЫЕ ЗАПАСЫ (Inventory)
  const totalInventoryValue = inventory.reduce((sum, i) => sum + (parseFloat(i.value) || 0), 0);
  
  // 4. НДС (VAT)
  const totalVATReceivable = Object.values(monthlyData).reduce((sum, m) => sum + m.income_vat, 0);
  const totalVATPayable = Object.values(monthlyData).reduce((sum, m) => sum + m.expense_vat, 0);
  const netVAT = totalVATReceivable - totalVATPayable;
  
  // 5. ОБЩИЕ ПОКАЗАТЕЛИ
  const totalIncome = Object.values(monthlyData).reduce((sum, m) => sum + m.income, 0);
  const totalExpense = Object.values(monthlyData).reduce((sum, m) => sum + m.expense, 0);
  const totalProfit = totalIncome - totalExpense;
  const profitMargin = totalIncome !== 0 ? ((totalProfit / totalIncome) * 100).toFixed(2) : 0;
  
  // 6. АКТИВЫ И ПАССИВЫ (для баланса)
  const assets = {
    cash: runningBalance, // Остаток денежных средств
    inventory: totalInventoryValue,
    receivables: 0, // TODO: добавить дебиторку
    total: runningBalance + totalInventoryValue
  };
  
  const liabilities = {
    debts: totalDebts,
    payables: 0, // TODO: добавить кредиторку
    vat_payable: netVAT > 0 ? 0 : Math.abs(netVAT),
    total: totalDebts + (netVAT > 0 ? 0 : Math.abs(netVAT))
  };
  
  const equity = assets.total - liabilities.total;
  
  return {
    monthlyData,
    dailyData,
    totalDebts,
    overdueDebts,
    activeDebts,
    totalInventoryValue,
    totalIncome,
    totalExpense,
    totalProfit,
    profitMargin,
    vat: {
      receivable: totalVATReceivable,
      payable: totalVATPayable,
      net: netVAT
    },
    balance: {
      assets,
      liabilities,
      equity
    },
    transactions,
    debts,
    inventory,
    revenue,
    budgets
  };
};

export default {
  getTransactions,
  addTransaction,
  updateTransaction,
  deleteTransaction,
  getDebts,
  addDebt,
  updateDebt,
  deleteDebt,
  getInventory,
  addInventoryItem,
  updateInventoryItem,
  deleteInventoryItem,
  getRevenue,
  setMonthlyRevenue,
  getExpenses,
  addExpense,
  updateExpense,
  deleteExpense,
  calculateFinancialData
};
