import Link from "next/link";

const BOT_CLIENT_ID = process.env.NEXT_PUBLIC_BOT_CLIENT_ID ?? "YOUR_BOT_CLIENT_ID";
const INVITE_URL = `https://discord.com/oauth2/authorize?client_id=${BOT_CLIENT_ID}&permissions=8&integration_type=0&scope=bot+applications.commands`;

export default function Footer() {
  return (
    <footer className="bg-gray-950 border-t border-white/5 text-gray-400 text-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 text-white font-bold text-lg mb-3">
              <span className="text-2xl">🏒</span>
              <span>Hockey Bot</span>
            </div>
            <p className="text-gray-500 text-sm leading-relaxed">
              Discord&apos;s premier NHL statistics bot. Real-time scores,
              standings, schedules, and trivia.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-white font-semibold mb-3">Links</h3>
            <ul className="space-y-2">
              <li><Link href="/#features" className="hover:text-white transition-colors">Features</Link></li>
              <li><Link href="/updates" className="hover:text-white transition-colors">Updates</Link></li>
              <li><Link href="https://discord.gg/WGQYdzvn8y" target="_blank" className="hover:text-white transition-colors">Discord Server</Link></li>
              <li>
                <Link
                  href={INVITE_URL}
                  target="_blank"
                  className="hover:text-white transition-colors"
                >
                  Add to Server
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-white font-semibold mb-3">Legal</h3>
            <ul className="space-y-2">
              <li><Link href="/tos" className="hover:text-white transition-colors">Terms of Service</Link></li>
              <li><Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-2">
          <p>© {new Date().getFullYear()} Hockey Bot. Built by <span className="text-white">@jzcob</span>.</p>
          <p>Not affiliated with the NHL.</p>
        </div>
      </div>
    </footer>
  );
}
