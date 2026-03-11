import { auth } from "@/lib/auth";
import { NextResponse } from "next/server";

const DISCORD_API = "https://discord.com/api/v10";

// Permissions flag for "Manage Guild" (0x20)
const MANAGE_GUILD = 0x20;

export async function GET() {
  const session = await auth();

  if (!session?.accessToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const res = await fetch(`${DISCORD_API}/users/@me/guilds`, {
      headers: {
        Authorization: `Bearer ${session.accessToken}`,
      },
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: "Failed to fetch guilds from Discord" },
        { status: res.status }
      );
    }

    const guilds: {
      id: string;
      name: string;
      icon: string | null;
      owner: boolean;
      permissions: string;
    }[] = await res.json();

    // Only return guilds where the user can manage the server
    const manageableGuilds = guilds.filter(
      (g) => (Number(g.permissions) & MANAGE_GUILD) === MANAGE_GUILD
    );

    return NextResponse.json(manageableGuilds);
  } catch {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
