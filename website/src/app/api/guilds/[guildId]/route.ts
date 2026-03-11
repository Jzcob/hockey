import { auth } from "@/lib/auth";
import { NextRequest, NextResponse } from "next/server";
import mysql from "mysql2/promise";

const DISCORD_API = "https://discord.com/api/v10";
const MANAGE_GUILD = 0x20;

async function getConnection() {
  return mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
  });
}

async function userManagesGuild(
  accessToken: string,
  guildId: string
): Promise<boolean> {
  const res = await fetch(`${DISCORD_API}/users/@me/guilds`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!res.ok) return false;
  const guilds: { id: string; permissions: string }[] = await res.json();
  const guild = guilds.find((g) => g.id === guildId);
  if (!guild) return false;
  return (Number(guild.permissions) & MANAGE_GUILD) === MANAGE_GUILD;
}

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ guildId: string }> }
) {
  const session = await auth();
  if (!session?.accessToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { guildId } = await params;

  const hasAccess = await userManagesGuild(session.accessToken, guildId);
  if (!hasAccess) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  let conn: mysql.Connection | null = null;
  try {
    conn = await getConnection();
    const [rows] = await conn.execute(
      "SELECT * FROM guild_settings WHERE guild_id = ?",
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      [guildId] as any
    );
    const settings = (rows as mysql.RowDataPacket[])[0] ?? null;
    return NextResponse.json({ settings });
  } catch {
    return NextResponse.json(
      { error: "Database error" },
      { status: 500 }
    );
  } finally {
    if (conn) await conn.end();
  }
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ guildId: string }> }
) {
  const session = await auth();
  if (!session?.accessToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { guildId } = await params;

  const hasAccess = await userManagesGuild(session.accessToken, guildId);
  if (!hasAccess) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  let body: Record<string, unknown>;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const allowedKeys = [
    "welcome_channel_id",
    "welcome_message",
    "leave_channel_id",
    "leave_message",
    "log_channel_id",
    "prefix",
    "trivia_enabled",
    "levels_enabled",
  ];

  const updates: Record<string, unknown> = {};
  for (const key of allowedKeys) {
    if (key in body) updates[key] = body[key];
  }

  if (Object.keys(updates).length === 0) {
    return NextResponse.json(
      { error: "No valid fields to update" },
      { status: 400 }
    );
  }

  let conn: mysql.Connection | null = null;
  try {
    conn = await getConnection();

    const columns = Object.keys(updates);
    const setClauses = columns.map((k) => `${k} = ?`).join(", ");
    const insertCols = columns.join(", ");
    const insertPlaceholders = columns.map(() => "?").join(", ");
    const insertValues: unknown[] = Object.values(updates);

    const sql =
      `INSERT INTO guild_settings (guild_id, ${insertCols}) ` +
      `VALUES (?, ${insertPlaceholders}) ` +
      `ON DUPLICATE KEY UPDATE ${setClauses}`;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await conn.execute(sql, [guildId, ...insertValues, ...insertValues] as any);

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json(
      { error: "Database error" },
      { status: 500 }
    );
  } finally {
    if (conn) await conn.end();
  }
}
