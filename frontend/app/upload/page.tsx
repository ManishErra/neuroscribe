"use client"

import { useEffect, useState } from "react"

type Patient = {
  id: string
  name: string
  age: number
  gender: string
}

export default function UploadPage() {

  // =========================
  // STATE
  // =========================

  const [patients, setPatients] = useState<Patient[]>([])
  const [selectedPatientId, setSelectedPatientId] = useState("")

  const [sessionId, setSessionId] = useState("")

  const [transcript, setTranscript] = useState("")
  const [transcriptId, setTranscriptId] = useState("")

  const [note, setNote] = useState<any>(null)
  const [noteId, setNoteId] = useState("")

  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [saved, setSaved] = useState(false)

  const [error, setError] = useState("")

  // =========================
  // LOAD PATIENTS
  // =========================

  useEffect(() => {

    async function loadPatients() {

      try {

        const res = await fetch(
          "http://localhost:8000/patients/"
        )

        if (!res.ok) {
          throw new Error("Failed to load patients")
        }

        const data = await res.json()

        setPatients(data)

      } catch (err: any) {

        setError(err.message)
      }
    }

    loadPatients()

  }, [])

  // =========================
  // SELECTED PATIENT
  // =========================

  const selectedPatient = patients.find(
    p => p.id === selectedPatientId
  )

  // =========================
  // CREATE SESSION
  // =========================

  async function createSession() {

    if (!selectedPatientId) {
      setError("Please select a patient first")
      return null
    }

    try {

      const res = await fetch(
        "http://localhost:8000/sessions/",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            patient_id: selectedPatientId,
            session_date: new Date()
              .toISOString()
              .split("T")[0]
          })
        }
      )

      if (!res.ok) {
        throw new Error(await res.text())
      }

      const data = await res.json()

      setSessionId(data.id)

      return data.id

    } catch (err: any) {

      setError(err.message)
      return null
    }
  }

  // =========================
  // HANDLE AUDIO UPLOAD
  // =========================

  async function handleUpload(
    e: React.ChangeEvent<HTMLInputElement>
  ) {

    const file = e.target.files?.[0]

    if (!file) return

    if (!selectedPatientId) {
      setError("Please select a patient first")
      return
    }

    // Reset old state
    setLoading(true)
    setError("")

    setTranscript("")
    setTranscriptId("")

    setNote(null)
    setNoteId("")

    setSaved(false)

    try {

      // =========================
      // Create new session
      // =========================

      const newSessionId = await createSession()

      if (!newSessionId) {
        throw new Error("Failed to create session")
      }

      // =========================
      // Upload audio
      // =========================

      const form = new FormData()

      form.append("file", file)

      form.append(
        "session_id",
        newSessionId
      )

      const res = await fetch(
        "http://localhost:8000/upload-audio",
        {
          method: "POST",
          body: form
        }
      )

      if (!res.ok) {
        throw new Error(await res.text())
      }

      const data = await res.json()

      setTranscript(data.transcript)

      setTranscriptId(data.transcript_id)

    } catch (err: any) {

      setError(err.message)

    } finally {

      setLoading(false)
    }
  }

  // =========================
  // GENERATE NOTE
  // =========================

  async function generateNote() {

    if (!selectedPatient) {
      setError("Patient not selected")
      return
    }

    if (!transcriptId) {
      setError("Transcript missing")
      return
    }

    setGenerating(true)

    setError("")

    try {

      const res = await fetch(
        "http://localhost:8000/generate-note",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            transcript_id: transcriptId,
            patient_name: selectedPatient.name,
            patient_age: selectedPatient.age
          })
        }
      )

      if (!res.ok) {
        throw new Error(await res.text())
      }

      const data = await res.json()

      setNote(data.ai_draft)

      setNoteId(data.note_id)

    } catch (err: any) {

      setError(err.message)

    } finally {

      setGenerating(false)
    }
  }

  // =========================
  // SAVE NOTE
  // =========================

  async function saveNote() {

    try {

      const res = await fetch(
        "http://localhost:8000/save-note",
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json"
          },

          body: JSON.stringify({
            note_id: noteId,
            doctor_edited: note
          })
        }
      )

      if (!res.ok) {
        throw new Error(await res.text())
      }

      setSaved(true)

    } catch (err: any) {

      setError(err.message)
    }
  }

  // =========================
  // UI
  // =========================

  return (

    <main className="p-8 max-w-2xl mx-auto space-y-6">

      <h1 className="text-xl font-medium">
        Upload Session Audio
      </h1>

      {/* PATIENT SELECT */}

      <div>

        <label className="text-sm font-medium block mb-2">
          Select Patient
        </label>

        <select
          value={selectedPatientId}
          onChange={(e) =>
            setSelectedPatientId(e.target.value)
          }
          className="w-full border rounded p-2 text-sm"
        >

          <option value="">
            Choose patient...
          </option>

          {patients.map(patient => (

            <option
              key={patient.id}
              value={patient.id}
            >
              {patient.name} ({patient.age})
            </option>

          ))}

        </select>

      </div>

      {/* FILE INPUT */}

      <input
        type="file"
        accept=".mp3,.wav,.m4a"
        onChange={handleUpload}
        className="border p-2 rounded w-full text-sm"
      />

      {/* STATUS */}

      {loading && (
        <p className="text-blue-500 text-sm">
          Transcribing audio...
        </p>
      )}

      {error && (
        <p className="text-red-500 text-sm">
          {error}
        </p>
      )}

      {/* TRANSCRIPT */}

      {transcript && (

        <div>

          <div className="flex items-center gap-2 mb-2">

            <h2 className="font-medium text-sm">
              Transcript
            </h2>

            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
              AI Generated
            </span>

          </div>

          <textarea
            readOnly
            value={transcript}
            className="w-full h-40 border rounded p-3 text-sm text-gray-700 bg-gray-50"
          />

          <button
            onClick={generateNote}
            disabled={generating}
            className="mt-3 px-4 py-2 bg-blue-600 text-white rounded text-sm disabled:opacity-50"
          >
            {generating
              ? "Generating Clinical Note..."
              : "Generate Clinical Note"}
          </button>

        </div>
      )}

      {/* NOTE EDITOR */}

      {note && !saved && (

        <div>

          <div className="flex items-center gap-2 mb-3">

            <h2 className="font-medium">
              Clinical Note
            </h2>

            <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">
              AI Draft — Review Required
            </span>

          </div>

          {Object.entries(note).map(([key, value]) => (

            <div
              key={key}
              className="mb-4"
            >

              <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">

                {key.replace(/_/g, " ")}

              </label>

              <textarea
                value={
                  Array.isArray(value)
                    ? value.join(", ")
                    : String(value)
                }

                onChange={(e) =>
                  setNote({
                    ...note,
                    [key]: e.target.value
                  })
                }

                className="w-full border rounded p-2 text-sm mt-1 min-h-[70px]"
              />

            </div>

          ))}

          <button
            onClick={saveNote}
            className="px-4 py-2 bg-green-600 text-white rounded text-sm"
          >
            ✓ Mark as Reviewed & Save
          </button>

        </div>
      )}

      {/* SUCCESS */}

      {saved && (

        <div className="bg-green-50 border border-green-200 rounded p-4 text-green-700 text-sm">

          ✓ Note reviewed and saved successfully.

        </div>
      )}

      {/* DEBUG SESSION */}

      {sessionId && (

        <div className="text-xs text-gray-500 border-t pt-4">

          Session ID: {sessionId}

        </div>
      )}

    </main>
  )
}