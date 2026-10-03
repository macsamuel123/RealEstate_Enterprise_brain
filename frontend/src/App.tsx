import { useState } from 'react';
import { Nav, NavTab } from '@/components/Nav';
import { Home } from '@/pages/Home';
import { BusinessHealth } from '@/pages/BusinessHealth';
import { Today } from '@/pages/Today';
import { Approvals } from '@/pages/Approvals';
import { Agents } from '@/pages/Agents';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState<NavTab>('home');

  const renderPage = () => {
    switch (activeTab) {
      case 'home':
        return <Home />;
      case 'business-health':
        return <BusinessHealth />;
      case 'today':
        return <Today />;
      case 'approvals':
        return <Approvals />;
      case 'agents':
        return <Agents />;
      default:
        return <Home />;
    }
  };

  return (
    <div className="app">
      <div className="app-content">{renderPage()}</div>
      <Nav active={activeTab} onTabChange={setActiveTab} />
    </div>
  );
}

export default App;
