// 404 Not Found page.
// Architecture ref: frontend_architecture.md §4 (path: "*")

import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { AlertOctagon } from 'lucide-react';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div
      id="not-found-page"
      className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground px-6"
    >
      <AlertOctagon className="h-12 w-12 text-muted-foreground opacity-40 mb-4" />
      <h1 className="text-2xl font-bold tracking-tight mb-2">404 — Page not found</h1>
      <p className="text-sm text-muted-foreground mb-6 text-center max-w-xs">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <Button id="not-found-home" onClick={() => navigate('/')} variant="outline">
        Return to Dashboard
      </Button>
    </div>
  );
}
