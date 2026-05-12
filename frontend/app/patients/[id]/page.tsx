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

type SearchSource = {
  date: string
  similarity?: number
  excerpt: string
}

type SearchAnswer = {
  answer: string
  sources: SearchSource[]
  citation_verified: boolean
  query: string
  retrieved_chunks?: number
}

export default function PatientDetailPage() {

  const params = useParams()

  const patientId = params.id as string

  // =====================================
  // MAIN STATE
  // =====================================

  const [patient, setPatient] =
    useState<Patient | null>(null)

  const [sessions, setSessions] =
    useState<Session[]>([])

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState("")

  // =====================================
  // RAG SEARCH STATE
  // =====================================

  const [query, setQuery] =
    useState("")

  const [answer, setAnswer] =
    useState<SearchAnswer | null>(null)

  const [searching, setSearching] =
    useState(false)

  // =====================================
  // LOAD DATA
  // =====================================

  useEffect(() => {

    async function loadData() {

      try {

        setLoading(true)

        const patientRes = await fetch(
          `http://localhost:8000/patients/${patientId}`
        )

        if (!patientRes.ok) {
          throw new Error("Patient not found")
        }

        const patientData =
          await patientRes.json()

        setPatient(patientData)

        const sessionRes = await fetch(
          `http://localhost:8000/sessions/patient/${patientId}`
        )

        if (sessionRes.ok) {

          const sessionData =
            await sessionRes.json()

          setSessions(sessionData)
        }

      } catch (err: any) {

        setError(
          err.message ||
          "Failed to load patient"
        )

      } finally {

        setLoading(false)
      }
    }

    if (patientId) {
      loadData()
    }

  }, [patientId])

  // =====================================
  // CREATE SESSION
  // =====================================

  async function createSession() {

    try {

      setError("")

      const today =
        new Date()
          .toISOString()
          .split("T")[0]

      const res = await fetch(
        "http://localhost:8000/sessions/",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            patient_id: patientId,
            session_date: today
          })
        }
      )

      if (!res.ok) {
        throw new Error(await res.text())
      }

      const sessionRes = await fetch(
        `http://localhost:8000/sessions/patient/${patientId}`
      )

      if (sessionRes.ok) {

        const sessionData =
          await sessionRes.json()

        setSessions(sessionData)
      }

    } catch (err: any) {

      setError(
        err.message ||
        "Failed to create session"
      )
    }
  }

  // =====================================
  // ASK QUESTION
  // =====================================

  async function askQuestion() {

    if (!query.trim()) return

    try {

      setSearching(true)

      setAnswer(null)

      setError("")

      const res = await fetch(
        "http://localhost:8000/search/ask",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            query: query.trim(),
            patient_id: patientId
          })
        }
      )

      if (!res.ok) {
        throw new Error(await res.text())
      }

      const data = await res.json()

      setAnswer(data)

    } catch {

      setAnswer({

        answer:
          "Search failed. Try again.",

        sources: [],

        citation_verified: false,

        query
      })

    } finally {

      setSearching(false)
    }
  }

  // =====================================
  // LOADING
  // =====================================

  if (loading) {

    return (

      <main className="min-h-screen bg-black text-zinc-100 p-8">

        <div className="max-w-4xl mx-auto">

          <div className="
            animate-pulse
            h-40
            rounded-3xl
            bg-zinc-900
          " />

        </div>

      </main>
    )
  }

  // =====================================
  // ERROR
  // =====================================

  if (error) {

    return (

      <main className="
        min-h-screen
        bg-black
        text-zinc-100
        p-8
      ">

        <div className="max-w-3xl mx-auto">

          <div className="
            bg-red-500/10
            border border-red-500/20
            rounded-2xl
            p-5
          ">

            <p className="text-red-300 text-sm">
              {error}
            </p>

          </div>

        </div>

      </main>
    )
  }

  // =====================================
  // MAIN UI
  // =====================================

  return (

    <main className="
      min-h-screen
      bg-black
      text-zinc-100
      px-6 py-10
    ">

      <div className="max-w-4xl mx-auto">

        {/* ================================
            HEADER
        ================================= */}

        <div className="
          relative overflow-hidden
          border border-white/10
          bg-gradient-to-br
          from-zinc-950
          to-zinc-900
          rounded-3xl
          p-8
          shadow-2xl
          mb-10
        ">

          <div className="
            absolute
            top-0 right-0
            w-40 h-40
            bg-blue-500/10
            blur-3xl
            rounded-full
          " />

          <div className="relative z-10">

            <h1 className="
              text-4xl
              font-bold
              tracking-tight
            ">

              {patient?.name}

            </h1>

            <p className="
              text-zinc-400
              mt-3
              text-base
            ">

              {patient?.age} yrs · {patient?.gender}

            </p>

          </div>

        </div>

        {/* ================================
            SESSION HEADER
        ================================= */}

        <div className="
          flex items-center
          justify-between
          mb-5
        ">

          <div>

            <h2 className="
              text-2xl
              font-semibold
            ">

              Sessions

            </h2>

            <p className="
              text-sm
              text-zinc-500
              mt-1
            ">

              Clinical interaction history

            </p>

          </div>

          <button
            onClick={createSession}
            className="
              px-5 py-3
              bg-blue-600
              hover:bg-blue-500
              active:scale-[0.98]
              transition-all
              rounded-2xl
              text-sm
              font-medium
              shadow-lg shadow-blue-500/20
            "
          >

            + New Session

          </button>

        </div>

        {/* ================================
            EMPTY STATE
        ================================= */}

        {sessions.length === 0 && (

          <div className="
            border border-dashed
            border-zinc-700
            rounded-3xl
            bg-zinc-950
            p-14
            text-center
          ">

            <p className="
              text-zinc-500
              text-sm
            ">

              No sessions available yet.

            </p>

          </div>
        )}

        {/* ================================
            SESSION LIST
        ================================= */}

        <div className="space-y-4">

          {sessions.map((session) => (

            <div
              key={session.id}
              className="
                group
                border border-white/10
                bg-zinc-950/70
                hover:bg-zinc-900/80
                transition-all duration-200
                rounded-3xl
                p-5
                backdrop-blur-sm
              "
            >

              <div className="
                flex items-start
                justify-between
                gap-4
              ">

                <div>

                  <p className="
                    text-base
                    font-semibold
                    text-zinc-100
                  ">

                    Session

                  </p>

                  <p className="
                    text-xs
                    text-zinc-500
                    mt-2
                    font-mono
                    break-all
                  ">

                    {session.id}

                  </p>

                  <p className="
                    text-sm
                    text-zinc-400
                    mt-3
                  ">

                    {session.session_date}

                  </p>

                </div>

                <div className="
                  flex gap-2
                  flex-wrap
                  justify-end
                ">

                  {session.has_note ? (

                    <span className="
                      text-xs
                      bg-green-500/15
                      text-green-300
                      border border-green-500/20
                      px-3 py-1.5
                      rounded-full
                    ">

                      Note Exists

                    </span>

                  ) : (

                    <span className="
                      text-xs
                      bg-zinc-800
                      text-zinc-400
                      px-3 py-1.5
                      rounded-full
                    ">

                      No Note

                    </span>

                  )}

                  {session.note_finalized && (

                    <span className="
                      text-xs
                      bg-blue-500/15
                      text-blue-300
                      border border-blue-500/20
                      px-3 py-1.5
                      rounded-full
                    ">

                      Finalized

                    </span>

                  )}

                </div>

              </div>

            </div>
          ))}

        </div>

        {/* ================================
            AI SEARCH
        ================================= */}

        <div className="
          mt-14
          border-t border-zinc-800
          pt-10
        ">

          <div className="mb-5">

            <h2 className="
              text-lg
              font-semibold
            ">

              Ask About This Patient

            </h2>

            <p className="
              text-sm
              text-zinc-500
              mt-1
            ">

              Semantic retrieval over clinical history

            </p>

          </div>

          {/* SEARCH BAR */}

          <div className="
            flex gap-3
            items-center
          ">

            <input
              value={query}

              onChange={(e) =>
                setQuery(e.target.value)
              }

              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  askQuestion()
                }
              }}

              placeholder="e.g. what medications were mentioned?"

              className="
                flex-1
                bg-zinc-900/80
                border border-zinc-700
                rounded-2xl
                px-5 py-4
                text-sm
                text-zinc-100
                placeholder:text-zinc-500
                focus:outline-none
                focus:ring-2
                focus:ring-blue-500/50
                focus:border-blue-500
                transition-all
              "
            />

            <button
              onClick={askQuestion}

              disabled={searching}

              className="
                px-6 py-4
                bg-blue-600
                hover:bg-blue-500
                active:scale-[0.98]
                transition-all
                rounded-2xl
                text-sm
                font-medium
                shadow-lg
                shadow-blue-500/20
                disabled:opacity-50
              "
            >

              {searching
                ? "Searching..."
                : "Ask"}

            </button>

          </div>

          {/* ANSWER */}

          {answer && (

            <div className="mt-7 space-y-5">

              {/* ANSWER CARD */}

              <div className="
                border border-white/10
                bg-gradient-to-br
                from-zinc-900
                to-zinc-950
                rounded-3xl
                p-6
              ">

                <div className="
                  flex items-center
                  gap-2
                  flex-wrap
                  mb-5
                ">

                  <span className="
                    text-sm
                    font-semibold
                    text-zinc-200
                  ">

                    AI Clinical Answer

                  </span>

                  <span className="
                    text-xs
                    bg-blue-500/15
                    text-blue-300
                    border border-blue-500/20
                    px-2.5 py-1
                    rounded-full
                  ">

                    RAG

                  </span>

                  {!answer.citation_verified && (

                    <span className="
                      text-xs
                      bg-yellow-500/15
                      text-yellow-300
                      border border-yellow-500/20
                      px-2.5 py-1
                      rounded-full
                    ">

                      Citation Missing

                    </span>

                  )}

                </div>

                <p className="
                  text-[15px]
                  leading-8
                  text-zinc-100
                  whitespace-pre-wrap
                ">

                  {answer.answer}

                </p>

              </div>

              {/* SOURCES */}

              {answer.sources?.length > 0 && (

                <div>

                  <p className="
                    text-xs
                    uppercase
                    tracking-[0.2em]
                    text-zinc-500
                    mb-4
                  ">

                    Sources

                  </p>

                  <div className="space-y-3">

                    {answer.sources.map(
                      (source, index) => (

                        <div
                          key={index}
                          className="
                            group
                            bg-zinc-950
                            border border-white/10
                            hover:border-zinc-600
                            transition-all
                            rounded-2xl
                            p-5
                          "
                        >

                          <div className="
                            flex items-center
                            justify-between
                            mb-4
                          ">

                            <p className="
                              text-sm
                              font-medium
                              text-zinc-300
                            ">

                              {source.date}

                            </p>

                            {source.similarity && (

                              <span className="
                                text-xs
                                bg-zinc-800
                                text-zinc-300
                                px-3 py-1
                                rounded-full
                              ">

                                similarity:
                                {" "}
                                {source.similarity.toFixed(3)}

                              </span>

                            )}

                          </div>

                          <p className="
                            text-sm
                            text-zinc-400
                            leading-7
                            break-words
                          ">

                            {source.excerpt}

                          </p>

                        </div>
                      )
                    )}

                  </div>

                </div>
              )}

            </div>
          )}

        </div>

      </div>

    </main>
  )
}