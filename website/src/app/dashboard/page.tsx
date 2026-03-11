"use client";

import { useSession, signIn } from "next-auth/react";
import { useEffect, useState } from "react";
import Link from "next/link";

const BOT_CLIENT_ID = process.env.NEXT_PUBLIC_BOT_CLIENT_ID ?? "YOUR_BOT_CLIENT_ID";
const INVITE_URL = `https://discord.com/oauth2/authorize?client_id=${BOT_CLIENT_ID}&permissions=8&integration_type=0&scope=bot+applications.commands`;

interface Guild {
  id: string;
  name: string;
  icon: string | null;
  owner: boolean;
  permissions: string;
}

function guildIconUrl(guild: Guild) {
  if (!guild.icon) return null;
  return `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.png?size=64`;
}

export default function DashboardPage() {
  const { status } = useSession();
  const [guilds, setGuilds] = useState<Guild[]>([]);
  const [fetchDone, setFetchDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "authenticated") {
      fetch("/api/guilds")
        .then((res) => res.json())
        .then((data) => {
          if (Array.isArray(data)) {
            setGuilds(data);
          } else {
            setError("Failed to load servers.");
          }
        })
        .catch(() => setError("Failed to load servers."))
        .finally(() => setFetchDone(true));
    }
  }, [status]);

  const loading =
    status === "loading" || (status === "authenticated" && !fetchDone);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-400">Loading...</div>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-6 px-4 text-center">
        <div className="text-6xl">🔒</div>
        <h1 className="text-3xl font-bold text-white">Sign in to continue</h1>
        <p className="text-gray-400 max-w-sm">
          Log in with your Discord account to manage Hockey Bot settings for
          your servers.
        </p>
        <button
          onClick={() => signIn("discord")}
          className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-colors text-lg"
        >
          Login with Discord
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-16 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="mb-10">
          <h1 className="text-3xl font-bold text-white mb-2">Your Servers</h1>
          <p className="text-gray-400">
            Select a server to configure Hockey Bot settings. Only servers where
            you have &ldquo;Manage Server&rdquo; permission are shown.
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-gray-400">Loading your servers...</div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
            {error}
          </div>
        )}

        {!loading && !error && guilds.length === 0 && (
          <div className="text-center py-20">
            <div className="text-5xl mb-4">🏒</div>
            <h2 className="text-xl font-semibold text-white mb-2">
              No manageable servers found
            </h2>
            <p className="text-gray-400 mb-6">
              You don&apos;t have Manage Server permission in any servers with Hockey
              Bot, or the bot hasn&apos;t been added yet.
            </p>
            <Link
              href={INVITE_URL}
              target="_blank"
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
            >
              Add Hockey Bot to a Server
            </Link>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {guilds.map((guild) => {
            const iconUrl = guildIconUrl(guild);
            return (
              <Link
                key={guild.id}
                href={`/dashboard/${guild.id}`}
                className="flex items-center gap-4 p-4 rounded-2xl bg-white/[0.03] border border-white/[0.08] hover:border-indigo-500/50 hover:bg-white/[0.06] transition-all group"
              >
                {iconUrl ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={iconUrl}
                    alt={guild.name}
                    className="w-12 h-12 rounded-full border border-white/10"
                  />
                ) : (
                  <div className="w-12 h-12 rounded-full bg-indigo-600/30 flex items-center justify-center text-xl font-bold text-indigo-300 border border-indigo-500/20">
                    {guild.name.charAt(0)}
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-white truncate group-hover:text-indigo-300 transition-colors">
                    {guild.name}
                  </p>
                  {guild.owner && (
                    <p className="text-xs text-gray-500 mt-0.5">Owner</p>
                  )}
                </div>
                <svg
                  className="w-4 h-4 text-gray-500 group-hover:text-indigo-400 transition-colors flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
