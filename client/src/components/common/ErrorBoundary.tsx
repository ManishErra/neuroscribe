// Error boundary — catches unhandled render errors and shows fallback UI.
// Architecture ref: frontend_architecture.md §11.2 (components/common/ErrorBoundary)

import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[NeuroScribe ErrorBoundary]', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center min-h-[40vh] px-6">
          <Alert variant="destructive" className="max-w-md w-full">
            <AlertDescription>
              <p className="font-medium mb-1">Something went wrong</p>
              <p className="text-xs opacity-80 mb-3 font-mono break-all">
                {this.state.error?.message ?? 'Unknown error'}
              </p>
              <Button
                id="error-boundary-reset"
                variant="outline"
                size="sm"
                onClick={this.handleReset}
              >
                Try again
              </Button>
            </AlertDescription>
          </Alert>
        </div>
      );
    }

    return this.props.children;
  }
}
