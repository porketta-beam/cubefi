import PortfolioChart from './PortfolioChart';
import TaxBotWidget from './TaxBotWidget';

export default function Dashboard() {
  return (
    <div className="dashboard-container">
      <h1>Stock D-TAX 대시보드</h1>
      <PortfolioChart />
      <TaxBotWidget />
    </div>
  );
} 