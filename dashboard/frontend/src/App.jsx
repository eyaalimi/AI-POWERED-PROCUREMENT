import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import KpisPage from './pages/KpisPage';
import PipelinesPage from './pages/PipelinesPage';
import ActivityPage from './pages/ActivityPage';
import SuppliersPage from './pages/SuppliersPage';
import BlacklistPage from './pages/BlacklistPage';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<KpisPage />} />
            <Route path="/pipelines" element={<PipelinesPage />} />
            <Route path="/activity" element={<ActivityPage />} />
            <Route path="/suppliers" element={<SuppliersPage />} />
            <Route path="/blacklist" element={<BlacklistPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
