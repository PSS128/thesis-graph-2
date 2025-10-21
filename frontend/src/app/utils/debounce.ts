/**
 * Debounce utility to prevent rapid repeated function calls
 */

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null

  return function debounced(...args: Parameters<T>) {
    if (timeout) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(() => {
      func(...args)
      timeout = null
    }, wait)
  }
}

/**
 * Throttle utility to limit function execution rate
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false

  return function throttled(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => {
        inThrottle = false
      }, limit)
    }
  }
}

/**
 * Request deduplication - prevents identical requests from running concurrently
 */
export class RequestDeduplicator {
  private pendingRequests: Map<string, Promise<any>> = new Map()

  /**
   * Execute a function only if it's not already running with the same key
   */
  async dedupe<T>(key: string, fn: () => Promise<T>): Promise<T> {
    // If request is already pending, return existing promise
    if (this.pendingRequests.has(key)) {
      return this.pendingRequests.get(key)!
    }

    // Execute new request
    const promise = fn().finally(() => {
      // Clean up when done
      this.pendingRequests.delete(key)
    })

    this.pendingRequests.set(key, promise)
    return promise
  }

  /**
   * Clear all pending requests
   */
  clear() {
    this.pendingRequests.clear()
  }
}
