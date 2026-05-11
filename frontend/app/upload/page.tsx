"use client"
import { useState } from "react"

export default function UploadPage() {
  const [transcript, setTranscript] = useState("")
  const [transcriptId, setTranscriptId] = useState("")
  const [note, setNote] = useState<any>(null)
  const [noteId, setNoteId] = useState("")
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState("")

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setLoading(true); setError(""); setTranscript(""); setNote(null)
    const form = new FormData()
    form.append("file", file)
    try {
      const res = await fetch("http://localhost:8000/upload-audio",
        { method: "POST", body: form })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setTranscript(data.transcript)
      setTranscriptId(data.transcript_id)
    } catch (err: any) { setError(err.message) }
    finally { setLoading(false) }
  }

  async function generateNote() {
    setGenerating(true); setError("")
    try {
      const res = await fetch("http://localhost:8000/generate-note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transcript_id: transcriptId,
          patient_name: "Test Patient",
          patient_age: 35
        })
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setNote(data.ai_draft)
      setNoteId(data.note_id)
    } catch (err: any) { setError(err.message) }
    finally { setGenerating(false) }
  }

  async function saveNote() {
    try {
      const res = await fetch("http://localhost:8000/save-note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ note_id: noteId, doctor_edited: note })
      })
      if (!res.ok) throw new Error(await res.text())
      setSaved(true)
    } catch (err: any) { setError(err.message) }
  }

  return (
    <main className="p-8 max-w-2xl mx-auto space-y-6">
      <h1 className="text-xl font-medium">Upload Session Audio</h1>

      <input type="file" accept=".mp3,.wav,.m4a" onChange={handleUpload}
        className="border p-2 rounded w-full text-sm" />

      {loading && <p className="text-blue-500 text-sm">Transcribing...</p>}
      {error && <p className="text-red-500 text-sm">{error}</p>}

      {transcript && (
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="font-medium text-sm">Transcript</h2>
            <span className="text-xs bg-blue-100 text-blue-700
              px-2 py-0.5 rounded-full">AI Generated</span>
          </div>
          <textarea readOnly value={transcript}
            className="w-full h-32 border rounded p-3 text-sm
              text-gray-600 bg-gray-50" />
          <button onClick={generateNote} disabled={generating}
            className="mt-2 px-4 py-2 bg-blue-600 text-white
              rounded text-sm disabled:opacity-50">
            {generating ? "Generating..." : "Generate Clinical Note"}
          </button>
        </div>
      )}

      {note && !saved && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <h2 className="font-medium">Clinical Note</h2>
            <span className="text-xs bg-yellow-100 text-yellow-700
              px-2 py-0.5 rounded-full">AI Draft — Review Required</span>
          </div>
          {Object.entries(note).map(([key, value]) => (
            <div key={key} className="mb-3">
              <label className="text-xs font-medium text-gray-500
                uppercase tracking-wide">{key.replace(/_/g," ")}</label>
              <textarea
                value={Array.isArray(value)
                  ? (value as string[]).join(", ")
                  : String(value)}
                onChange={e => setNote({...note, [key]: e.target.value})}
                className="w-full border rounded p-2 text-sm mt-1 min-h-[60px]"
              />
            </div>
          ))}
          <button onClick={saveNote}
            className="px-4 py-2 bg-green-600 text-white rounded text-sm">
            ✓ Mark as Reviewed & Save
          </button>
        </div>
      )}

      {saved && (
        <div className="bg-green-50 border border-green-200
          rounded p-4 text-green-700 text-sm">
          ✓ Note reviewed and saved. Visible in patient history.
        </div>
      )}
    </main>
  )
}