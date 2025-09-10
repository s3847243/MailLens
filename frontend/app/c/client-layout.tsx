// app/chat/ClientLayout.tsx
"use client";
import { SidebarTrigger, useSidebar } from "@/components/ui/sidebar";
import { usePathname } from "next/navigation";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import { SearchEmails } from "@/components/search/Search";
import { useChatSessions } from "@/context/ChatSessionContext";
export default  function ClientLayout({ children }: { children: React.ReactNode }) {
  const { open } = useSidebar();
  const { chatSessions, refreshChats, deleteSession } = useChatSessions()
  const pathname = usePathname();
  const router = useRouter();
  useEffect(() => { void refreshChats() }, [refreshChats]) 



  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId) 
      if (pathname === `/c/${sessionId}`) router.replace('/c')
    } catch (e) {
      console.error('Delete failed:', e)
    }
  }
  
  return (
    <div className="flex h-screen w-full overflow-hidden">
      
      <div className="flex">
          <div className={`${open ? 'w-60' : 'w-0'}  border-gray-200 bg-white transition-all duration-300 overflow-hidden  `}>
            <AppSidebar  onDeleteSession={handleDeleteSession} chatSessions={chatSessions} />
          </div>
          
          <div     className={`relative z-10 mt-3 flex items-start justify-center shrink-0
                ${open ? "w-6 -ml-3" : "w-8 ml-0"}`} >
            <SidebarTrigger />
          </div>
      </div>

    
      <div className={`${open ? 'flex-[4]' : 'flex-[5]'} transition-all duration-300 flex flex-col relative`}>
       
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>

      <div className="flex-[1.5] border-l border-gray-200 bg-white overflow-auto">
        <SearchEmails />
      </div>
    </div>
    
  );
}