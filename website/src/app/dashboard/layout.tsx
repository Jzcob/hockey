import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — Hockey Bot",
  description: "Manage Hockey Bot settings for your Discord servers.",
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
