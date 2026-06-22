import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import Analyze from './pages/Analyze';
import Results from './pages/Results';
import Chat from './pages/Chat';
import Benefits from './pages/Benefits';

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/analyze" element={<Analyze />} />
          <Route path="/results" element={<Results />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/benefits" element={<Benefits />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
