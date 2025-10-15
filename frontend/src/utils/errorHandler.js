/**
 * Глобальный обработчик ошибок для подавления спама в консоли
 */

// Список паттернов ошибок, которые нужно игнорировать
const IGNORED_ERROR_PATTERNS = [
  'refreshUniformsCommon',
  'refreshMaterialUniforms',
  'WebGLRenderer',
  'renderBufferDirect',
  'Cannot read properties of undefined'
];

// Оригинальные методы консоли
const originalError = console.error;
const originalWarn = console.warn;

// Функция проверки, нужно ли игнорировать ошибку
const shouldIgnoreError = (message) => {
  const messageStr = String(message);
  return IGNORED_ERROR_PATTERNS.some(pattern => 
    messageStr.includes(pattern)
  );
};

// Переопределяем console.error
console.error = (...args) => {
  // Если это ошибка Three.js/WebGL - игнорируем
  if (args.some(arg => shouldIgnoreError(arg))) {
    return;
  }
  // Иначе выводим как обычно
  originalError.apply(console, args);
};

// Переопределяем console.warn
console.warn = (...args) => {
  if (args.some(arg => shouldIgnoreError(arg))) {
    return;
  }
  originalWarn.apply(console, args);
};

// Глобальный обработчик необработанных промисов
window.addEventListener('unhandledrejection', (event) => {
  if (shouldIgnoreError(event.reason)) {
    event.preventDefault();
  }
});

// Глобальный обработчик ошибок
window.addEventListener('error', (event) => {
  if (shouldIgnoreError(event.message || event.error)) {
    event.preventDefault();
  }
});

export default {
  init: () => {
    console.log('✅ Error handler initialized - WebGL spam suppressed');
  }
};
