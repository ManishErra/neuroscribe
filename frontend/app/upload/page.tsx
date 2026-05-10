"use client"
import { useState } from "react"

export default function UploadPage() {
  const [transcript, setTranscript] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return

    setLoading(true)
    setError("")
    setTranscript("")

    const form = new FormData()
    form.append("file", file)

    try {
      const res = await fetch("http://localhost:8000/upload-audio", {
        method: "POST",
        body: form,
      })

      if (!res.ok) throw new Error(await res.text())

      const data = await res.json()
      setTranscript(data.transcript)

    } catch (err: any) {
      setError(err.message)

    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="p-8 max-w-2xl mx-auto">
      <h1 className="text-xl font-medium mb-4">
        Upload Session Audio
      </h1>

      <input
        type="file"
        accept=".mp3,.wav,.m4a"
        onChange={handleUpload}
        className="border p-2 rounded w-full text-sm"
      />

      {loading && (
        <p className="mt-4 text-blue-500">
          Transcribing...
        </p>
      )}

      {error && (
        <p className="mt-4 text-red-500">
          {error}
        </p>
      )}

      {transcript && (
        <div className="mt-6">
          <div className="flex items-center gap-2 mb-2">
            <h2 className="font-medium">
              Transcript
            </h2>

            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
              AI Generated
            </span>
          </div>

          <textarea
            readOnly
            value={transcript}
            className="w-full h-48 border rounded p-3 text-sm text-gray-700"
          />
        </div>
      )}
    </main>
  )
}