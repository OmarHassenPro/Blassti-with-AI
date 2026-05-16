// ─────────────────────────────────────────────────────────────────────────────
// eventBackendSync.js
//
// Fire-and-forget sync helper for mirroring frontend event changes to the
// local Python backend JSON store.
//
// Rules:
//   - Never throws.
//   - Never blocks the existing UI/localStorage flow.
//   - If the backend is offline, the site keeps working exactly as before.
//   - Used only by src/dataModel/event.js.
// ─────────────────────────────────────────────────────────────────────────────

const BASE_URL = "http://localhost:5000/api"
const TIMEOUT_MS = 1500

function createTimeoutSignal(ms) {
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), ms)

  return {
    signal: controller.signal,
    clear() {
      window.clearTimeout(timer)
    },
  }
}

function cloneForTransport(value) {
  try {
    return JSON.parse(JSON.stringify(value))
  } catch (error) {
    console.warn("[eventBackendSync] Failed to clone payload for transport:", error?.message || error)
    return null
  }
}

async function silentRequest(method, path, body = null) {
  const { signal, clear } = createTimeoutSignal(TIMEOUT_MS)

  try {
    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
      },
      signal,
    }

    if (body !== null) {
      const preparedBody = cloneForTransport(body)

      if (preparedBody === null) {
        return
      }

      options.body = JSON.stringify(preparedBody)
    }

    await fetch(`${BASE_URL}${path}`, options)
  } catch (error) {
    console.warn(
      `[eventBackendSync] ${method} ${path} failed silently:`,
      error?.message || error
    )
  } finally {
    clear()
  }
}

export function syncAllEventsToBackend(eventList = []) {
  const { signal, clear } = createTimeoutSignal(TIMEOUT_MS)

  fetch(`${BASE_URL}/is-initialised`, { signal })
    .then(response => {
      if (!response.ok) {
        return null
      }

      return response.json()
    })
    .then(data => {
      const backendIsEmpty =
        !data ||
        !data.initialised ||
        Number(data.event_count || 0) === 0

      if (backendIsEmpty) {
        return silentRequest("POST", "/sync-events", {
          source: "frontend_event_model_initial_sync",
          events: Array.isArray(eventList) ? eventList : [],
        })
      }

      return null
    })
    .catch(error => {
      console.warn(
        "[eventBackendSync] Initial sync check failed:",
        error?.message || error
      )
    })
    .finally(() => {
      clear()
    })
}

export function syncAddEvent(event) {
  silentRequest("POST", "/events", event)
}

export function syncUpdateEvent(id, event) {
  silentRequest("PUT", `/events/${id}`, event)
}

export function syncDeleteEvent(id) {
  silentRequest("DELETE", `/events/${id}`)
}