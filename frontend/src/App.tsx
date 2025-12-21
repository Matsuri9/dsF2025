import { HashRouter, Routes, Route } from 'react-router-dom';
import { GlobePage } from './pages/GlobePage';
import { ComparisonPage } from './pages/ComparisonPage';
import './App.css';

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<GlobePage />} />
        <Route path="/compare" element={<ComparisonPage />} />
        <Route path="/compare/:lang1/:lang2" element={<ComparisonPage />} />
      </Routes>
    </HashRouter>
  );
}

export default App;
