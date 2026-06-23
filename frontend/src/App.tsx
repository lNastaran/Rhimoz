import { Link, Route, Routes } from 'react-router-dom';
import { TranscribePage } from './pages/TranscribePage';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';
import { DashboardPage } from './pages/DashboardPage';
import { ReopenedTranscriptionPage } from './pages/ReopenedTranscriptionPage';

function App() {
  return (
    <main>
      <h1>Rhimoz</h1>
      <nav style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
        <Link to="/">Transcribe</Link>
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/login">Log in</Link>
        <Link to="/signup">Sign up</Link>
      </nav>
      <Routes>
        <Route path="/" element={<TranscribePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/saved/:id" element={<ReopenedTranscriptionPage />} />
      </Routes>
    </main>
  );
}

export default App;
