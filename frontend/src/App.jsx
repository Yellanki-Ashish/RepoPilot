import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import Repository from "./pages/Repository";
import Assistant from "./pages/Assistant";
import Onboarding from "./pages/Onboarding";
import Issues from "./pages/Issues";

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/repository" element={<Repository />} />
          <Route path="/assistant" element={<Assistant />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/issues" element={<Issues />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
    </div>
  );
}
