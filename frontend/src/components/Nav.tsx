import './Nav.css';

export type NavTab = 'home' | 'business-health' | 'today' | 'approvals' | 'agents';

interface NavProps {
  active: NavTab;
  onTabChange: (tab: NavTab) => void;
}

export const Nav = ({ active, onTabChange }: NavProps) => {
  const tabs: { id: NavTab; label: string; icon: string }[] = [
    { id: 'home', label: 'Home', icon: '🏠' },
    { id: 'business-health', label: 'Health', icon: '📊' },
    { id: 'today', label: 'Today', icon: '📅' },
    { id: 'approvals', label: 'Approvals', icon: '✓' },
    { id: 'agents', label: 'Agents', icon: '🤖' },
  ];

  return (
    <nav className="nav">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`nav-tab ${active === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
          title={tab.label}
        >
          <span className="nav-icon">{tab.icon}</span>
          <span className="nav-label">{tab.label}</span>
        </button>
      ))}
    </nav>
  );
};
