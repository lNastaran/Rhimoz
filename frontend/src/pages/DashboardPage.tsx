import { Navigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';

export function DashboardPage() {
  const { session, isLoading, signOut } = useAuth();

  if (isLoading) return null;
  if (!session) return <Navigate to="/login" replace />;

  return (
    <div>
      <p>Logged in as {session.user.email}.</p>
      <button onClick={() => void signOut()}>Log out</button>
      <p>Saved transcriptions - coming soon.</p>
    </div>
  );
}
