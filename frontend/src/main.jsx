import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App.jsx";
import { RepositoryProvider } from "./hooks/useRepository";
import "./styles/global.css";
import "./styles/navbar.css";
import "./styles/dashboard.css";
import "./styles/chat.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <RepositoryProvider>
        <App />
      </RepositoryProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
