import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";
import errorHandler from "./utils/errorHandler";

// Инициализируем обработчик ошибок для подавления спама WebGL/Three.js
errorHandler.init();

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
