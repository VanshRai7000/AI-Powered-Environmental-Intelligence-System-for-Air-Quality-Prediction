import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
    children: ReactNode;
}

interface State {
    hasError: boolean;
    errorMessage: string | null;
}

export default class ErrorBoundary extends Component<Props, State> {
    state: State = {
        hasError: false,
        errorMessage: null,
    };

    static getDerivedStateFromError(error: Error): State {
        return {
            hasError: true,
            errorMessage: error.message || "An unexpected UI error occurred.",
        };
    }

    componentDidCatch(error: Error, info: ErrorInfo) {
        console.error("Dashboard ErrorBoundary caught:", error, info);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
                    <div className="max-w-md w-full bg-white border border-rose-200 rounded-2xl p-6 shadow-sm text-center space-y-4">
                        <div className="w-12 h-12 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto text-xl">
                            ⚠️
                        </div>
                        <h2 className="text-lg font-bold text-slate-900">Something went wrong</h2>
                        <p className="text-sm text-slate-600">
                            {this.state.errorMessage}
                        </p>
                        <button
                            type="button"
                            onClick={() => window.location.reload()}
                            className="px-4 py-2 bg-slate-900 text-white text-sm font-medium rounded-lg hover:bg-slate-800 transition-colors cursor-pointer"
                        >
                            Reload Dashboard
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

