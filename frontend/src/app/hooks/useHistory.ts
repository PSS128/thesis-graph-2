import { useState, useCallback, useRef } from 'react'

type HistoryState<T> = {
  past: T[]
  present: T
  future: T[]
}

export function useHistory<T>(initialState: T) {
  const [state, setState] = useState<HistoryState<T>>({
    past: [],
    present: initialState,
    future: []
  })

  const lastRecordedTime = useRef<number>(Date.now())
  const THROTTLE_MS = 500 // Don't record more than once every 500ms

  const set = useCallback((newPresent: T, force = false) => {
    setState((currentState) => {
      // Throttle to avoid recording too many states during rapid changes
      const now = Date.now()
      if (!force && now - lastRecordedTime.current < THROTTLE_MS) {
        // Update present without recording to history
        return {
          ...currentState,
          present: newPresent
        }
      }

      lastRecordedTime.current = now

      // If the new state is the same as current, don't record
      if (JSON.stringify(currentState.present) === JSON.stringify(newPresent)) {
        return currentState
      }

      return {
        past: [...currentState.past, currentState.present],
        present: newPresent,
        future: [] // Clear future when a new action is taken
      }
    })
  }, [])

  const undo = useCallback(() => {
    setState((currentState) => {
      if (currentState.past.length === 0) return currentState

      const previous = currentState.past[currentState.past.length - 1]
      const newPast = currentState.past.slice(0, currentState.past.length - 1)

      return {
        past: newPast,
        present: previous,
        future: [currentState.present, ...currentState.future]
      }
    })
  }, [])

  const redo = useCallback(() => {
    setState((currentState) => {
      if (currentState.future.length === 0) return currentState

      const next = currentState.future[0]
      const newFuture = currentState.future.slice(1)

      return {
        past: [...currentState.past, currentState.present],
        present: next,
        future: newFuture
      }
    })
  }, [])

  const reset = useCallback((newPresent: T) => {
    setState({
      past: [],
      present: newPresent,
      future: []
    })
  }, [])

  const canUndo = state.past.length > 0
  const canRedo = state.future.length > 0

  return {
    state: state.present,
    set,
    undo,
    redo,
    reset,
    canUndo,
    canRedo
  }
}
