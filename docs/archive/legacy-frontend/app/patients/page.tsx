"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { apiRequest } from "../../lib/api"

type Patient = {
  id: string
  name: string
  age: number
  gender: string
}

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const data = await apiRequest("/patients/");
        if (Array.isArray(data)) {
          setPatients(data);
        } else {
          setPatients([]);
        }
      } catch (err: any) {
        setError(err.message || "Failed to load patients list.");
        setPatients([]);
      } finally {
        setLoading(false);
      }
    };
    fetchPatients();
  }, [])

  return (
    <main className="p-8 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl font-medium">Patients</h1>

        <Link
          href="/patients/new"
          className="px-4 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
        >
          + Add Patient
        </Link>
      </div>

      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/25 p-4 mb-6 text-sm font-medium text-red-400">
          {error}
        </div>
      )}

      {loading && (
        <p className="text-gray-400 text-sm">
          Loading...
        </p>
      )}

      {!loading && patients.length === 0 && (
        <div className="border border-dashed rounded-lg p-8 text-center text-gray-400">
          <p className="text-sm">No patients yet.</p>

          <Link
            href="/patients/new"
            className="text-blue-500 text-sm mt-2 inline-block"
          >
            Add your first patient →
          </Link>
        </div>
      )}

      <div className="space-y-2">
        {patients.map((p) => (
          <Link
            key={p.id}
            href={`/patients/${p.id}`}
            className="block border rounded-lg p-4 hover:bg-gray-50 transition-colors"
          >
            <div className="flex justify-between items-center">
              <div>
                <p className="font-medium text-sm">
                  {p.name}
                </p>

                <p className="text-xs text-gray-400 mt-0.5">
                  {p.age} yrs · {p.gender}
                </p>
              </div>

              <span className="text-gray-300 text-sm">
                →
              </span>
            </div>
          </Link>
        ))}
      </div>
    </main>
  )
}