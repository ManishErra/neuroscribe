"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"

export default function NewPatientPage() {
  const router = useRouter()
  const [form, setForm] = useState({
    name: "", age: "", gender: "Male"
  })
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)

  async function handleSubmit() {
    if (!form.name.trim() || !form.age) {
      setError("Name and age are required"); return
    }
    setSaving(true); setError("")
    try {
      const res = await fetch("http://localhost:8000/patients/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: form.name,
          age: parseInt(form.age),
          gender: form.gender
        })
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      // Redirect to patient detail page
      router.push(`/patients/${data.id}`)
    } catch (err: any) {
      setError(err.message)
    } finally { setSaving(false) }
  }

  return (
    <main className="p-8 max-w-md mx-auto">
      <h1 className="text-xl font-medium mb-6">Add New Patient</h1>

      <div className="space-y-4">
        <div>
          <label className="text-xs font-medium text-gray-500
            uppercase tracking-wide block mb-1">Full Name *</label>
          <input type="text" value={form.name}
            onChange={e => setForm({...form, name: e.target.value})}
            placeholder="e.g. Rahul Sharma"
            className="w-full border rounded px-3 py-2 text-sm" />
        </div>

        <div>
          <label className="text-xs font-medium text-gray-500
            uppercase tracking-wide block mb-1">Age *</label>
          <input type="number" value={form.age} min="1" max="120"
            onChange={e => setForm({...form, age: e.target.value})}
            placeholder="e.g. 35"
            className="w-full border rounded px-3 py-2 text-sm" />
        </div>

        <div>
          <label className="text-xs font-medium text-gray-500
            uppercase tracking-wide block mb-1">Gender</label>
          <select value={form.gender}
            onChange={e => setForm({...form, gender: e.target.value})}
            className="w-full border rounded px-3 py-2 text-sm">
            <option>Male</option>
            <option>Female</option>
            <option>Other</option>
          </select>
        </div>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        <div className="flex gap-3 pt-2">
          <button onClick={handleSubmit} disabled={saving}
            className="flex-1 py-2 bg-blue-600 text-white rounded
              text-sm disabled:opacity-50">
            {saving ? "Saving..." : "Save Patient"}
          </button>
          <button onClick={() => router.push("/patients")}
            className="px-4 py-2 border rounded text-sm">
            Cancel
          </button>
        </div>
      </div>
    </main>
  )
}