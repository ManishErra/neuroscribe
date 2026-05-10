"use client"

import { useState } from "react"

export default function Home() {
  const [status, setStatus] = useState("")

  async function ping() {
    const res = await fetch("http://localhost:8000/")
    const data = await res.json()
    setStatus(data.message)
  }

  return (
    <main className="p-8">
      <h1 className="text-2xl font-medium">
        NeuroScribe
      </h1>

      <p className="text-gray-500 mt-2">
        AI Psychiatric Workflow Assistant
      </p>

      <button
        onClick={ping}
        className="mt-4 px-4 py-2 border rounded text-sm"
      >
        Ping backend
      </button>

      {status && (
        <p className="mt-2 text-green-600">
          {status}
        </p>
      )}
    </main>
  )
}