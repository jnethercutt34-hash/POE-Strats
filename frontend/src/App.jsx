import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import MechanicsList from './pages/MechanicsList';
import MechanicDetail from './pages/MechanicDetail';
import Economy from './pages/Economy';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-[var(--poe-bg)]">
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/mechanics" element={<MechanicsList />} />
          <Route path="/mechanics/:name" element={<MechanicDetail />} />
          <Route path="/economy" element={<Economy />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
