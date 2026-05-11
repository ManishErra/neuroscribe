"use client"

import { useEffect, useState } from "react"
import { useParams } from "next/navigation"

type Patient = {
  id: string
  name: string
  age: number
  gender: string
}

type Session = {
  id: string
  session_date: string
  has_note?: boolean
  note_finalized?: boolean
}

export default function PatientDetailPage() {
  const params = useParams()
  const patientId = params.id as string

  const [patient, setPatient] = useState<Patient | null>(null)
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    async function loadData() {
      try {

        // Load patient info
        const patientRes = await fetch(
          `http://localhost:8000/patients/${patientId}`
        )

        if (!patientRes.ok) {
          throw new Error("Patient not found")
        }

        const patientData = await patientRes.json()
        setPatient(patientData)

        // Load sessions
        const sessionRes = await fetch(
          `http://localhost:8000/sessions/patient/${patientId}`
        )

        if (sessionRes.ok) {
          const sessionData = await sessionRes.json()
          setSessions(sessionData)
        }

      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }

    if (patientId) {
      loadData()
    }
  }, [patientId])

  async function createSession() {
    try {

      const today = new Date().toISOString().split("T")[0]

      const res = await fetch("http://localhost:8000/sessions/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          patient_id: patientId,
          session_date: today
        })
      })

      if (!res.ok) {
        throw new Error(await res.text())
      }

      // Reload sessions after creating
      const sessionRes = await fetch(
        `http://localhost:8000/sessions/patient/${patientId}`
      )

      if (sessionRes.ok) {
        const sessionData = await sessionRes.json()
        setSessions(sessionData)
      }

    } catch (err: any) {
      setError(err.message)
    }
  }

  if (loading) {
    return (
      <main className="p-8">
        <p className="text-sm text-gray-400">
          Loading...
        </p>
      </main>
    )
  }

  if (error) {
    return (
      <main className="p-8">
        <p className="text-red-500 text-sm">
          {error}
        </p>
      </main>
    )
  }

  return (
    <main className="p-8 max-w-2xl mx-auto">

      {/* Patient Header */}
      <div className="border rounded-lg p-6 mb-6">
        <h1 className="text-2xl font-semibold">
          {patient?.name}
        </h1>

        <p className="text-gray-500 mt-2 text-sm">
          {patient?.age} yrs · {patient?.gender}
        </p>
      </div>

      {/* Sessions Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium">
          Sessions
        </h2>

        <button
          onClick={createSession}
          className="px-4 py-2 bg-blue-600 text-white rounded text-sm"
        >
          + New Session
        </button>
      </div>

      {/* Empty State */}
      {sessions.length === 0 && (
        <div className="border border-dashed rounded-lg p-8 text-center text-gray-400">
          <p className="text-sm">
            No sessions yet.
          </p>
        </div>
      )}

      {/* Sessions List */}
      <div className="space-y-3">
        {sessions.map((session) => (
          <div
            key={session.id}
            className="border rounded-lg p-4"
          >
            <p className="font-medium text-sm">
              Session
            </p>

            <p className="text-xs text-gray-400 mt-1 break-all">
              {session.id}
            </p>

            <p className="text-xs text-gray-500 mt-2">
              Date: {session.session_date}
            </p>

            <div className="mt-2 flex gap-2">
              {session.has_note ? (
                <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                  Note Exists
                </span>
              ) : (
                <span className="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded">
                  No Note
                </span>
              )}

              {session.note_finalized && (
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                  Finalized
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

    </main>
  )
}