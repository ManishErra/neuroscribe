import Link from "next/link"

export default function Navbar() {
  return (
    <nav className="border-b px-8 py-3 flex items-center gap-6">
      <Link
        href="/"
        className="font-medium text-sm"
      >
        NeuroScribe
      </Link>

      <Link
        href="/patients"
        className="text-sm text-gray-500 hover:text-gray-900"
      >
        Patients
      </Link>

      <Link
        href="/upload"
        className="text-sm text-gray-500 hover:text-gray-900"
      >
        Upload Session
      </Link>
    </nav>
  )
}