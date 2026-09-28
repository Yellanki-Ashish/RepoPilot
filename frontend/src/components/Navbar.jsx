import { NavLink } from "react-router-dom";
import { Bug, Compass, GitBranch, LayoutDashboard, MessageSquare } from "lucide-react";
import { useRepository } from "../hooks/useRepository";

const links = [
  { to: "/repository", label: "Dashboard", icon: LayoutDashboard },
  { to: "/assistant", label: "Assistant", icon: MessageSquare },
  { to: "/onboarding", label: "Onboarding", icon: Compass },
  { to: "/issues", label: "Issues", icon: Bug },
];

export default function Navbar() {
  const { repo } = useRepository();
  return (
    <header className="navbar">
      <NavLink to="/" className="brand">
        <span className="brand-logo"><GitBranch size={18} /></span>
        <span>RepoPilot</span>
      </NavLink>
      <nav className="nav-links">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
            <Icon size={16} /> <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="nav-repo">{repo ? repo.repository.full_name : "No repository loaded"}</div>
    </header>
  );
}
