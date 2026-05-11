"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"

type SessionData = {
  id: string
  session_date: string
  transcript: string | null
  note: Record<string, any> | null
  note_finalized: boolean
}

export default function SessionDetailPage() {

  // =========================
  // ROUTE PARAMS
  // =========================

  const params = useParams()

  const sessionId = params.id as string

  // =========================
  // STATE
  // =========================

  const [session, setSession] =
    useState<SessionData | null>(null)

  const [loading, setLoading] = useState(true)

  const [error, setError] = useState("")

  // =========================
  // LOAD SESSION
  // =========================

  useEffect(() => {

    async function loadSession() {

      try {

        setLoading(true)

        const res = await fetch(
          `http://localhost:8000/sessions/${sessionId}`
        )

        if (!res.ok) {
          throw new Error("Failed to load session")
        }

        const data = await res.json()

        setSession(data)

      } catch (err: any) {

        setError(err.message)

      } finally {

        setLoading(false)
      }
    }

    if (sessionId) {
      loadSession()
    }

  }, [sessionId])

  // =========================
  // LOADING STATE
  // =========================

  if (loading) {

    return (

      <main className="p-8">

        <p className="text-sm text-gray-400">
          Loading session...
        </p>

      </main>
    )
  }

  // =========================
  // ERROR STATE
  // =========================

  if (error) {

    return (

      <main className="p-8">

        <p className="text-red-500 text-sm">
          {error}
        </p>

      </main>
    )
  }

  // =========================
  // SESSION NOT FOUND
  // =========================

  if (!session) {

    return (

      <main className="p-8">

        <p className="text-sm text-gray-400">
          Session not found
        </p>

      </main>
    )
  }

  // =========================
  // UI
  // =========================

  return (

    <main className="p-8 max-w-4xl mx-auto space-y-6">

      {/* ========================= */}
      {/* SESSION HEADER */}
      {/* ========================= */}

      <div className="border border-zinc-700 rounded-lg p-6 bg-zinc-950">

        <h1 className="text-2xl font-semibold text-white">
          Therapy Session
        </h1>

        <p className="text-sm text-gray-400 mt-2">
          Session Date: {session.session_date}
        </p>

        <div className="mt-3">

          <span className="text-sm text-gray-400">
            Status:
          </span>

          {session.note_finalized ? (

            <span className="ml-2 text-sm text-green-500 font-medium">
              Finalized
            </span>

          ) : (

            <span className="ml-2 text-sm text-yellow-400 font-medium">
              Draft
            </span>

          )}

        </div>

      </div>

      {/* ========================= */}
      {/* TRANSCRIPT */}
      {/* ========================= */}

      <div className="border border-zinc-700 rounded-lg p-6 bg-zinc-950">

        <h2 className="font-medium mb-4 text-white">
          Transcript
        </h2>

        {session.transcript ? (

          <textarea
            readOnly
            value={session.transcript}
            className="
              w-full
              h-64
              border
              border-zinc-700
              rounded
              p-3
              text-sm
              bg-zinc-900
              text-white
              resize-none
              outline-none
            "
          />

        ) : (

          <p className="text-sm text-gray-400">
            No transcript available
          </p>

        )}

      </div>

      {/* ========================= */}
      {/* CLINICAL NOTE */}
      {/* ========================= */}

      <div className="border border-zinc-700 rounded-lg p-6 bg-zinc-950">

        <h2 className="font-medium mb-4 text-white">
          Clinical Note
        </h2>

        {session.note ? (

          <div className="space-y-5">

            {Object.entries(session.note).map(
              ([key, value]) => (

                <div key={key}>

                  <label className="
                    text-xs
                    font-medium
                    text-gray-400
                    uppercase
                    tracking-wide
                    block
                    mb-2
                  ">

                    {key.replace(/_/g, " ")}

                  </label>

                  <textarea
                    readOnly
                    value={
                      Array.isArray(value)
                        ? value.join(", ")
                        : String(value ?? "")
                    }
                    className="
                      w-full
                      border
                      border-zinc-700
                      rounded
                      p-3
                      text-sm
                      bg-zinc-900
                      text-white
                      min-h-[90px]
                      resize-none
                      outline-none
                    "
                  />

                </div>
              )
            )}

          </div>

        ) : (

          <p className="text-sm text-gray-400">
            No clinical note available
          </p>

        )}

      </div>

    </main>
  )
}