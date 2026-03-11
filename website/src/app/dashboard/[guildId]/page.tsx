"use client";

import { useSession, signIn } from "next-auth/react";
import { useEffect, useState, use } from "react";
import Link from "next/link";

interface GuildSettings {
  guild_id?: string;
  welcome_channel_id?: string;
  welcome_message?: string;
  leave_channel_id?: string;
  leave_message?: string;
  log_channel_id?: string;
  prefix?: string;
  trivia_enabled?: number;
  levels_enabled?: number;
}

interface FieldProps {
  label: string;
  description?: string;
  children: React.ReactNode;
}

function Field({ label, description, children }: FieldProps) {
  return (
    <div className="flex flex-col md:flex-row md:items-start gap-3 py-5 border-b border-white/[0.06]">
      <div className="md:w-64 flex-shrink-0">
        <p className="text-sm font-medium text-white">{label}</p>
        {description && (
          <p className="text-xs text-gray-500 mt-0.5">{description}</p>
        )}
      </div>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function TextInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full bg-white/[0.06] border border-white/[0.1] rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 transition-colors"
    />
  );
}

function Toggle({
  enabled,
  onChange,
}: {
  enabled: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
        enabled ? "bg-indigo-600" : "bg-white/10"
      }`}
      aria-pressed={enabled}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
          enabled ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

export default function GuildSettingsPage({
  params,
}: {
  params: Promise<{ guildId: string }>;
}) {
  const { guildId } = use(params);
  const { data: session, status } = useSession();

  const [settings, setSettings] = useState<GuildSettings>({
    welcome_channel_id: "",
    welcome_message: "",
    leave_channel_id: "",
    leave_message: "",
    log_channel_id: "",
    prefix: ";;",
    trivia_enabled: 1,
    levels_enabled: 1,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "success" | "error">("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === "authenticated") {
      fetch(`/api/guilds/${guildId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.settings) {
            setSettings((prev) => ({ ...prev, ...data.settings }));
          }
        })
        .catch(() => setError("Failed to load server settings."))
        .finally(() => setLoading(false));
    }
  }, [status, guildId]);

  async function handleSave() {
    setSaving(true);
    setSaveStatus("idle");
    try {
      const res = await fetch(`/api/guilds/${guildId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
      if (res.ok) {
        setSaveStatus("success");
        setTimeout(() => setSaveStatus("idle"), 3000);
      } else {
        setSaveStatus("error");
      }
    } catch {
      setSaveStatus("error");
    } finally {
      setSaving(false);
    }
  }

  if (status === "loading" || loading) {
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
        <button
          onClick={() => signIn("discord")}
          className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-xl transition-colors"
        >
          Login with Discord
        </button>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-4 text-center">
        <div className="text-5xl">⚠️</div>
        <h1 className="text-2xl font-bold text-white">Access Denied</h1>
        <p className="text-gray-400 max-w-sm">{error}</p>
        <Link href="/dashboard" className="text-indigo-400 hover:text-indigo-300">
          ← Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-16 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center gap-3">
          <Link
            href="/dashboard"
            className="text-gray-400 hover:text-white transition-colors text-sm flex items-center gap-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Dashboard
          </Link>
          <span className="text-gray-600">/</span>
          <span className="text-white text-sm font-medium">Server Settings</span>
        </div>

        <h1 className="text-3xl font-bold text-white mb-2">Server Settings</h1>
        <p className="text-gray-400 mb-10">
          Configure Hockey Bot for server <span className="text-white font-mono text-sm bg-white/5 px-1.5 py-0.5 rounded">{guildId}</span>
        </p>

        <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-6">
          {/* General */}
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-2">
            General
          </h2>

          <Field
            label="Command Prefix"
            description="The prefix used for text commands (default: ;;)"
          >
            <TextInput
              value={settings.prefix ?? ";;"}
              onChange={(v) => setSettings((s) => ({ ...s, prefix: v }))}
              placeholder=";;"
            />
          </Field>

          {/* Welcome */}
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mt-8 mb-2">
            Welcome Messages
          </h2>

          <Field
            label="Welcome Channel ID"
            description="The channel where welcome messages are sent."
          >
            <TextInput
              value={settings.welcome_channel_id ?? ""}
              onChange={(v) => setSettings((s) => ({ ...s, welcome_channel_id: v }))}
              placeholder="Channel ID (e.g. 123456789012345678)"
            />
          </Field>

          <Field
            label="Welcome Message"
            description="Use {user} to mention the new member, {server} for server name."
          >
            <textarea
              value={settings.welcome_message ?? ""}
              onChange={(e) =>
                setSettings((s) => ({ ...s, welcome_message: e.target.value }))
              }
              placeholder="Welcome {user} to {server}! 🏒"
              rows={3}
              className="w-full bg-white/[0.06] border border-white/[0.1] rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 transition-colors resize-none"
            />
          </Field>

          {/* Leave */}
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mt-8 mb-2">
            Leave Messages
          </h2>

          <Field
            label="Leave Channel ID"
            description="The channel where leave messages are sent."
          >
            <TextInput
              value={settings.leave_channel_id ?? ""}
              onChange={(v) => setSettings((s) => ({ ...s, leave_channel_id: v }))}
              placeholder="Channel ID (e.g. 123456789012345678)"
            />
          </Field>

          <Field
            label="Leave Message"
            description="Use {user} for the member's name, {server} for server name."
          >
            <textarea
              value={settings.leave_message ?? ""}
              onChange={(e) =>
                setSettings((s) => ({ ...s, leave_message: e.target.value }))
              }
              placeholder="{user} has left {server}."
              rows={3}
              className="w-full bg-white/[0.06] border border-white/[0.1] rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500/60 focus:ring-1 focus:ring-indigo-500/40 transition-colors resize-none"
            />
          </Field>

          {/* Logging */}
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mt-8 mb-2">
            Logging
          </h2>

          <Field
            label="Log Channel ID"
            description="Channel where moderation logs and bot events are sent."
          >
            <TextInput
              value={settings.log_channel_id ?? ""}
              onChange={(v) => setSettings((s) => ({ ...s, log_channel_id: v }))}
              placeholder="Channel ID (e.g. 123456789012345678)"
            />
          </Field>

          {/* Features */}
          <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mt-8 mb-2">
            Features
          </h2>

          <Field
            label="Trivia"
            description="Enable or disable the trivia game in this server."
          >
            <Toggle
              enabled={!!settings.trivia_enabled}
              onChange={(v) => setSettings((s) => ({ ...s, trivia_enabled: v ? 1 : 0 }))}
            />
          </Field>

          <Field
            label="Levels & XP"
            description="Enable or disable the leveling system in this server."
          >
            <Toggle
              enabled={!!settings.levels_enabled}
              onChange={(v) => setSettings((s) => ({ ...s, levels_enabled: v ? 1 : 0 }))}
            />
          </Field>
        </div>

        {/* Save button */}
        <div className="flex items-center justify-end gap-4 mt-6">
          {saveStatus === "success" && (
            <span className="text-green-400 text-sm">✓ Settings saved successfully</span>
          )}
          {saveStatus === "error" && (
            <span className="text-red-400 text-sm">Failed to save settings. Please try again.</span>
          )}
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors text-sm"
          >
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>

        {/* Note about session */}
        {session?.user?.name && (
          <p className="text-center text-gray-600 text-xs mt-8">
            Logged in as <span className="text-gray-400">{session.user.name}</span>
          </p>
        )}
      </div>
    </div>
  );
}
