import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Updates — Hockey Bot",
  description: "Latest updates, new features, and improvements to Hockey Bot.",
};

const updates = [
  {
    version: "v2.5.0",
    date: "January 2026",
    tag: "Major",
    tagColor: "bg-indigo-500/20 text-indigo-300",
    changes: [
      "🌐 Launched hockeybot.gg — official website with server management dashboard",
      "⚙️ New server dashboard: configure welcome messages, leave messages, and log channels",
      "🏒 Added Utah Hockey Club (Utah Mammoth) to all team commands",
      "📊 Improved player stat display with season-by-season breakdown",
    ],
  },
  {
    version: "v2.4.0",
    date: "October 2025",
    tag: "Feature",
    tagColor: "bg-green-500/20 text-green-300",
    changes: [
      "🎟️ Overhauled ticket system with improved threading",
      "🏆 Added Eastern and Western Conference filtered standings",
      "🎖️ Levels system: XP multipliers for premium guilds",
      "🐛 Fixed schedule command showing incorrect game times in non-ET timezones",
    ],
  },
  {
    version: "v2.3.0",
    date: "May 2025",
    tag: "Feature",
    tagColor: "bg-green-500/20 text-green-300",
    changes: [
      "🧠 Trivia: added 50+ new community-submitted questions",
      "📅 /tomorrow command now shows all games with live countdown",
      "🔔 Improved error messages and help documentation",
      "⚡ Performance: database connection pooling with 3600s recycle",
    ],
  },
  {
    version: "v2.2.0",
    date: "January 2025",
    tag: "Feature",
    tagColor: "bg-green-500/20 text-green-300",
    changes: [
      "💎 Launched Premium (Referee tier) via Discord Entitlements",
      "📈 Leaderboards now support global and server-scoped views",
      "🏒 /team command redesigned with improved embed layout",
      "🔧 Admin: new /servers command for bot owner diagnostics",
    ],
  },
  {
    version: "v2.1.0",
    date: "August 2024",
    tag: "Patch",
    tagColor: "bg-yellow-500/20 text-yellow-300",
    changes: [
      "📡 Migrated all data fetching to NHL API v1 (api-web.nhle.com)",
      "🐛 Fixed standings not updating after games end",
      "🎨 Consistent embed color scheme (#ffffff) across all commands",
    ],
  },
  {
    version: "v2.0.0",
    date: "January 2024",
    tag: "Major",
    tagColor: "bg-indigo-500/20 text-indigo-300",
    changes: [
      "✅ Bot verified on Discord App Directory",
      "🚀 Full migration to slash commands",
      "🗄️ Switched from file-based storage to MySQL database",
      "🧩 Modular cog architecture for all features",
      "🎫 Tickets system launch",
    ],
  },
  {
    version: "v1.0.0",
    date: "November 2023",
    tag: "Launch",
    tagColor: "bg-purple-500/20 text-purple-300",
    changes: [
      "🎉 Initial public release of Hockey Bot",
      "📅 Today's games, /standings, /schedule commands",
      "🏒 Basic team and player info",
      "🧠 Hockey trivia with /suggest-trivia",
    ],
  },
];

export default function UpdatesPage() {
  return (
    <div className="min-h-screen py-16 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="mb-12">
          <h1 className="text-4xl font-bold text-white mb-3">Updates &amp; Changelog</h1>
          <p className="text-gray-400 text-lg">
            Every new feature, improvement, and bug fix — all in one place.
          </p>
        </div>

        <div className="relative">
          <div className="absolute left-0 top-0 bottom-0 w-px bg-white/5 ml-[11px]" />

          <div className="space-y-10">
            {updates.map((update) => (
              <div key={update.version} className="relative pl-8">
                <div className="absolute left-0 top-2 w-6 h-6 rounded-full bg-gray-900 border-2 border-indigo-500 flex items-center justify-center">
                  <div className="w-2 h-2 rounded-full bg-indigo-400" />
                </div>

                <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6 hover:border-white/[0.15] transition-colors">
                  <div className="flex flex-wrap items-center gap-3 mb-4">
                    <h2 className="text-xl font-bold text-white">{update.version}</h2>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-semibold ${update.tagColor}`}
                    >
                      {update.tag}
                    </span>
                    <span className="text-gray-500 text-sm ml-auto">{update.date}</span>
                  </div>

                  <ul className="space-y-2">
                    {update.changes.map((change, i) => (
                      <li key={i} className="text-gray-300 text-sm leading-relaxed">
                        {change}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
