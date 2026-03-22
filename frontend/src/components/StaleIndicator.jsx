import { AlertTriangle, RefreshCw } from 'lucide-react';

/**
 * Banner shown when data is stale or retrying.
 */
export default function StaleIndicator({ isStale, retryCount, error, onRetry }) {
  if (!isStale && !error && retryCount === 0) return null;

  if (retryCount > 0) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-yellow-900/30 border border-yellow-700/50 px-4 py-2 text-yellow-300 text-sm">
        <RefreshCw className="w-4 h-4 animate-spin" />
        <span>Connection issue — retrying ({retryCount}/3)...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-red-900/30 border border-red-700/50 px-4 py-2 text-red-300 text-sm">
        <AlertTriangle className="w-4 h-4" />
        <span>Failed to load data: {error}</span>
        {onRetry && (
          <button
            onClick={onRetry}
            className="ml-auto px-3 py-1 rounded bg-red-700/50 hover:bg-red-700 text-red-100 text-xs transition-colors"
          >
            Retry
          </button>
        )}
      </div>
    );
  }

  if (isStale) {
    return (
      <div className="flex items-center gap-2 rounded-lg bg-yellow-900/20 border border-yellow-800/40 px-4 py-2 text-yellow-400 text-sm">
        <AlertTriangle className="w-4 h-4" />
        <span>Showing cached data — prices may be outdated</span>
        {onRetry && (
          <button
            onClick={onRetry}
            className="ml-auto px-3 py-1 rounded bg-yellow-700/40 hover:bg-yellow-700 text-yellow-100 text-xs transition-colors"
          >
            Refresh
          </button>
        )}
      </div>
    );
  }

  return null;
}
