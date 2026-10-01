"use client";

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useAuth } from "../context/AuthContext"

export default function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (pathname === "/login") return null;

  return (

    <nav className="
      sticky top-0 z-50
      border-b border-white/10
      bg-black/80
      backdrop-blur-xl
    ">

      <div className="
        max-w-6xl mx-auto
        px-6 py-4
        flex items-center
        justify-between
      ">

        {/* =========================
            LOGO
        ========================== */}

        <Link
          href="/"
          className="
            flex items-center gap-3
            group
          "
        >

          <div className="
            w-9 h-9
            rounded-xl
            bg-gradient-to-br
            from-blue-500
            to-cyan-400
            flex items-center
            justify-center
            shadow-lg
            shadow-blue-500/20
            group-hover:scale-105
            transition-transform
          ">

            <span className="
              text-black
              font-bold
              text-sm
            ">

              N

            </span>

          </div>

          <div>

            <p className="
              text-sm
              font-semibold
              tracking-wide
              text-white
            ">

              NeuroScribe

            </p>

            <p className="
              text-[11px]
              text-zinc-500
            ">

              AI Clinical Memory

            </p>

          </div>

        </Link>

        {/* =========================
            NAV LINKS
        ========================== */}

        <div className="
          flex items-center
          gap-2
        ">

          <Link
            href="/patients"
            className="
              text-sm
              text-zinc-400
              hover:text-white
              hover:bg-white/5
              transition-all
              px-4 py-2
              rounded-xl
            "
          >

            Patients

          </Link>

          <Link
            href="/upload"
            className="
              text-sm
              text-zinc-400
              hover:text-white
              hover:bg-white/5
              transition-all
              px-4 py-2
              rounded-xl
            "
          >

            Upload Session

          </Link>

          {user && (
            <>
              <div className="h-4 w-[1px] bg-white/10 mx-2"></div>
              <span className="text-xs text-zinc-500 font-medium px-1 max-w-[150px] truncate select-none">
                {user.name || user.email}
              </span>
              <button
                onClick={logout}
                className="
                  text-sm
                  text-red-400
                  hover:text-white
                  hover:bg-red-500/10
                  transition-all
                  px-4 py-2
                  rounded-xl
                "
              >
                Logout
              </button>
            </>
          )}

        </div>

      </div>

    </nav>
  )
}