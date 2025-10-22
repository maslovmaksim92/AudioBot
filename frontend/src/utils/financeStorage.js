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
  const newTransaction = {
    id: `trans-${Date.now()}`,
    ...transaction,
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

// Расходы (категории)
export const getExpenses = () => {
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

// Расчеты
export const calculateFinancialData = () => {
  const transactionsData = getTransactions();
  const debtsData = getDebts();
  const inventoryData = getInventory();
  const revenueData = getRevenue();
  
  // Убеждаемся что все данные это массивы
  const transactions = Array.isArray(transactionsData) ? transactionsData : [];
  const debts = Array.isArray(debtsData) ? debtsData : [];
  const inventory = Array.isArray(inventoryData) ? inventoryData : [];
  const revenue = Array.isArray(revenueData) ? revenueData : [];
  
  // Группируем транзакции по месяцам
  const monthlyData = {};
  
  transactions.forEach(t => {
    try {
      const date = new Date(t.date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      
      if (!monthlyData[monthKey]) {
        monthlyData[monthKey] = { income: 0, expense: 0 };
      }
      
      const amount = parseFloat(t.amount) || 0;
      
      if (t.type === 'income') {
        monthlyData[monthKey].income += amount;
      } else {
        monthlyData[monthKey].expense += amount;
      }
    } catch (e) {
      console.error('Error processing transaction:', e);
    }
  });
  
  // Добавляем ручную выручку
  revenue.forEach(r => {
    try {
      const [monthName, year] = r.month.split(' ');
      const monthIndex = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 
                         'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'].indexOf(monthName);
      const monthKey = `${year}-${String(monthIndex + 1).padStart(2, '0')}`;
      
      if (!monthlyData[monthKey]) {
        monthlyData[monthKey] = { income: 0, expense: 0 };
      }
      monthlyData[monthKey].income += parseFloat(r.amount) || 0;
    } catch (e) {
      console.error('Error processing revenue:', e);
    }
  });
  
  // Считаем итоги по задолженностям
  const totalDebts = debts
    .filter(d => d.status === 'active' || d.status === 'overdue')
    .reduce((sum, d) => sum + (parseFloat(d.amount) || 0), 0);
  const overdueDebts = debts
    .filter(d => d.status === 'overdue')
    .reduce((sum, d) => sum + (parseFloat(d.amount) || 0), 0);
  
  // Считаем стоимость запасов
  const totalInventoryValue = inventory.reduce((sum, i) => sum + (parseFloat(i.value) || 0), 0);
  
  return {
    monthlyData,
    totalDebts,
    overdueDebts,
    totalInventoryValue,
    transactions,
    debts,
    inventory,
    revenue
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
