import Link from "next/link";

const BOT_CLIENT_ID = process.env.NEXT_PUBLIC_BOT_CLIENT_ID ?? "YOUR_BOT_CLIENT_ID";

const INVITE_URL = `https://discord.com/oauth2/authorize?client_id=${BOT_CLIENT_ID}&permissions=8&integration_type=0&scope=bot+applications.commands`;

const features = [
  {
    icon: "📅",
    title: "Game Schedules",
    description:
      "Check today's, tomorrow's, or any team's upcoming schedule with a single command.",
  },
  {
    icon: "🏆",
    title: "Live Standings",
    description:
      "Up-to-date divisional and conference standings pulled directly from the NHL API.",
  },
  {
    icon: "🏒",
    title: "Team & Player Stats",
    description:
      "Deep-dive into any team or player with comprehensive stats and information.",
  },
  {
    icon: "🧠",
    title: "Hockey Trivia",
    description:
      "Test your knowledge with community-sourced trivia questions. Suggest your own with /suggest-trivia.",
  },
  {
    icon: "🎖️",
    title: "Levels & Leaderboards",
    description:
      "Engage your community with an XP leveling system and server leaderboards.",
  },
  {
    icon: "🎟️",
    title: "Ticket System",
    description:
      "Built-in support ticket system to handle user questions and issues in your server.",
  },
];

const milestones = [
  { label: "Released", date: "Nov 1, 2023" },
  { label: "Verified", date: "Jan 5, 2024" },
  { label: "100 Servers", date: "Jan 20, 2024" },
  { label: "500 Servers", date: "Oct 5, 2024" },
  { label: "1,000 Servers", date: "Jan 6, 2026" },
];

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden py-24 md:py-36 px-4">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-indigo-600/20 rounded-full blur-3xl" />
        </div>

        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 rounded-full bg-indigo-600/20 border border-indigo-500/30 text-indigo-400 text-sm font-medium">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
            Now on 1,000+ Discord servers
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 bg-gradient-to-br from-white via-gray-200 to-gray-400 bg-clip-text text-transparent">
            Hockey Bot
          </h1>

          <p className="text-xl md:text-2xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Discord&apos;s premier NHL statistics bot. Real-time scores, standings,
            schedules, and trivia — all in one place.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href={INVITE_URL}
              target="_blank"
              className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-colors text-lg shadow-lg shadow-indigo-900/40"
            >
              Add to Discord
            </Link>
            <Link
              href="https://discord.gg/WGQYdzvn8y"
              target="_blank"
              className="px-8 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-semibold rounded-xl transition-colors text-lg"
            >
              Join Support Server
            </Link>
          </div>
        </div>
      </section>

      {/* Stats bar */}
      <section className="border-y border-white/5 bg-white/[0.02] py-8 px-4">
        <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {[
            { value: "1,000+", label: "Servers" },
            { value: "32", label: "NHL Teams" },
            { value: "25+", label: "Commands" },
            { value: "2023", label: "Year Founded" },
          ].map((stat) => (
            <div key={stat.label}>
              <p className="text-3xl font-bold text-white">{stat.value}</p>
              <p className="text-gray-400 text-sm mt-1">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Everything your hockey community needs
            </h2>
            <p className="text-gray-400 max-w-xl mx-auto">
              From live game data to community engagement tools — Hockey Bot
              has it covered.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="p-6 rounded-2xl bg-white/[0.03] border border-white/[0.08] hover:border-white/[0.15] hover:bg-white/[0.05] transition-all"
              >
                <span className="text-4xl mb-4 block">{feature.icon}</span>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-400 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Milestones */}
      <section className="py-20 px-4 bg-white/[0.02] border-y border-white/5">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-3">Our Journey</h2>
            <p className="text-gray-400">Growing one server at a time.</p>
          </div>

          <div className="relative pl-8">
            <div className="absolute left-3 top-0 bottom-0 w-px bg-white/10" />
            <div className="space-y-8">
              {milestones.map((m) => (
                <div key={m.label} className="relative flex items-start gap-4">
                  <div className="absolute -left-5 top-1 w-3 h-3 rounded-full bg-indigo-500 border-2 border-indigo-300" />
                  <div>
                    <p className="font-semibold text-white">{m.label}</p>
                    <p className="text-gray-400 text-sm">{m.date}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-4 text-center">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to bring the rink to your server?
          </h2>
          <p className="text-gray-400 mb-8">
            Add Hockey Bot to your Discord server in seconds and start exploring
            NHL stats today.
          </p>
          <Link
            href={INVITE_URL}
            target="_blank"
            className="inline-block px-10 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-colors text-lg shadow-xl shadow-indigo-900/40"
          >
            Add Hockey Bot for Free
          </Link>
        </div>
      </section>
    </>
  );
}
