import ClientLayout from "./client-layout";
import { SidebarProvider } from "@/components/ui/sidebar";
import { UserProvider } from "@/context/UserContext";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ChatSessionsProvider } from "@/context/ChatSessionContext";
// server components do not forward cookie from next/headers, hence why fetch is being used to send reqs
async function getServerUser(cookieValue: string) {
  const res = await fetch('/api/me', {
    headers: { cookie: `maillens_session=${cookieValue}` },
    cache: 'no-store',
  })
  if (!res.ok) return null
  return res.json()
}

async function fetchChatSessions(cookieValue: string) {
  const res = await fetch('/api/chats', {
    headers: { cookie: `maillens_session=${cookieValue}` },
    cache: 'no-store',
  })
  if (!res.ok) return []
  return res.json()
}
export default async function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const cookieStore = await cookies();
  const token =cookieStore.get('maillens_session')?.value

  console.log("being redirected from token: ", token)
  if (!token) redirect("/"); 
  console.log("being redirected from user")
  const user = await getServerUser(token);
  if (!user) redirect('/');
  const initialChatSessions = await fetchChatSessions(token)
  return (
      <UserProvider initialUser={user}>
        <SidebarProvider defaultOpen={true}>
          <ChatSessionsProvider initial={initialChatSessions}>
          <ClientLayout>{children}</ClientLayout>
          </ChatSessionsProvider>
        </SidebarProvider>
      </UserProvider>

  );
}