"use client";

import Link from "next/link";
import { useSession, signIn, signOut } from "next-auth/react";
import { useState } from "react";

export default function Navbar() {
  const { data: session } = useSession();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="fixed top-0 w-full z-50 bg-gray-950/90 backdrop-blur-md border-b border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-white">
            <span className="text-2xl">🏒</span>
            <span>Hockey Bot</span>
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-6 text-sm text-gray-300">
            <Link href="/#features" className="hover:text-white transition-colors">Features</Link>
            <Link href="/updates" className="hover:text-white transition-colors">Updates</Link>
            <Link href="https://discord.gg/WGQYdzvn8y" target="_blank" className="hover:text-white transition-colors">Support</Link>
            {session && (
              <Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
            )}
          </div>

          {/* Auth button */}
          <div className="hidden md:flex items-center gap-3">
            {session ? (
              <div className="flex items-center gap-3">
                {session.user?.image && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={session.user.image}
                    alt={session.user.name ?? "User"}
                    className="w-8 h-8 rounded-full border border-white/20"
                  />
                )}
                <button
                  onClick={() => signOut()}
                  className="text-sm text-gray-300 hover:text-white transition-colors"
                >
                  Sign out
                </button>
              </div>
            ) : (
              <button
                onClick={() => signIn("discord")}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg font-medium transition-colors"
              >
                Login with Discord
              </button>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden text-gray-300 hover:text-white"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {mobileOpen ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-white/5 bg-gray-950 px-4 py-4 space-y-3 text-sm text-gray-300">
          <Link href="/#features" className="block hover:text-white" onClick={() => setMobileOpen(false)}>Features</Link>
          <Link href="/updates" className="block hover:text-white" onClick={() => setMobileOpen(false)}>Updates</Link>
          <Link href="https://discord.gg/WGQYdzvn8y" target="_blank" className="block hover:text-white" onClick={() => setMobileOpen(false)}>Support</Link>
          {session && (
            <Link href="/dashboard" className="block hover:text-white" onClick={() => setMobileOpen(false)}>Dashboard</Link>
          )}
          <div className="pt-2 border-t border-white/5">
            {session ? (
              <button onClick={() => signOut()} className="text-gray-300 hover:text-white">Sign out</button>
            ) : (
              <button onClick={() => signIn("discord")} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium">
                Login with Discord
              </button>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
