"use client";
import { useRouter } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupAction,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { Brain, BrainCircuit, Edit } from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@radix-ui/react-dropdown-menu"
import { Calendar, ChevronDown, ChevronUp, Home, Inbox, MoreHorizontal, Plus, Search, Settings, User2 } from "lucide-react"

import Link from "next/link"
import { ChatSession } from "@/types";
import { useState } from "react";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { useUser } from "@/context/UserContext";
import { logoutRequest } from "../api/userApi";
import { deleteUserAccount } from "../api/userApi";
export function AppSidebar({ onDeleteSession,chatSessions}: { onDeleteSession: (id: string) => Promise<void> | void; chatSessions:ChatSession[] }) {
    const { user } = useUser();
    const router = useRouter();
    // const [chats, setChats] = useState<ChatSession>();
    const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);
    // account delete dialog state
    const [confirmAccountOpen, setConfirmAccountOpen] = useState(false);
    const [isDeletingAccount, setIsDeletingAccount] = useState(false);
    
    const handleLogout = async () => {
      try {
        await logoutRequest();           
        router.replace("/"); 
      } catch (e) {
        console.error(e);
      }
    };
    
    const confirmDelete = async () => {
      if (!pendingDeleteId) return;
        setIsDeleting(true);
      try {
        await onDeleteSession(pendingDeleteId);
      } finally {
        setIsDeleting(false);
        setPendingDeleteId(null);
      }
    };
    const confirmDeleteAccount = async () => {
      setIsDeletingAccount(true);
      try {
        await deleteUserAccount();
        router.replace("/"); 
      } catch (e) {
        console.error("Account delete failed:", e);
      } finally {
        setIsDeletingAccount(false);
        setConfirmAccountOpen(false);
      }
    };
  return (
    <Sidebar>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            {
            /* <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton className="hover:bg-accent hover:text-accent-foreground transition-colors duration-200">
                 MailLens.AI 
                  <ChevronDown className="ml-auto transition-transform duration-200 group-data-[state=open]:rotate-180" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent 
                className="w-[--radix-popper-anchor-width] bg-white/100 border-2 border-purple-500 shadow-lg rounded-lg animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 p-2 z-50 backdrop-blur-none"
                sideOffset={4}
              >
                <DropdownMenuItem className="hover:bg-accent hover:text-accent-foreground cursor-pointer transition-colors duration-200 rounded-md px-2 py-1.5">
                  <button className="w-full text-left" >Delete Account</button>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu> 
            */}
            <SidebarGroupLabel className="text-xl font-bold text-gray-900 hover:underline">MailLens.AI</SidebarGroupLabel>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Projects</SidebarGroupLabel>
          <SidebarGroupAction title="Add Project">
            <Link href="/c" className="hover:bg-accent hover:text-accent-foreground transition-colors duration-200 rounded-md p-1">
              <Plus />
            </Link>
          </SidebarGroupAction>
          <SidebarGroupContent>
            <SidebarMenu>
              {chatSessions.map((item) => (
                <SidebarMenuItem key={item.id}>
                  <SidebarMenuButton asChild>
                    <Link 
                      href={`/c/${item.id}`} 
                      className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground transition-colors duration-200 rounded-md"
                    >
                      <Edit />
                      <span>{item.title || "Untitled Chat"}</span>
                    </Link>
                  </SidebarMenuButton>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <SidebarMenuAction className="hover:bg-accent hover:text-accent-foreground transition-colors duration-200">
                        <MoreHorizontal />
                      </SidebarMenuAction>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent 
                      side="right" 
                      align="start"
                      className="bg-white/100 border-2 border-purple-500 shadow-lg rounded-lg animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 p-2 z-50 backdrop-blur-none"
                      sideOffset={4}
                    >
                      <DropdownMenuItem className="hover:bg-accent hover:text-accent-foreground cursor-pointer transition-colors duration-200 rounded-md px-2 py-1.5">
                        <button className="w-full text-left" onClick={() => setPendingDeleteId(item.id)}>Delete Project</button>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton className="hover:bg-accent hover:text-accent-foreground transition-colors duration-200">
                  <User2 /> {user?.name || "Guest User"}
                  <ChevronUp className="ml-auto transition-transform duration-200 group-data-[state=open]:rotate-180" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side="top"
                className="w-[--radix-popper-anchor-width] bg-white/100 border-2 border-purple-500 shadow-lg rounded-lg animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 p-2 z-50 backdrop-blur-none"
                sideOffset={4}
              >
                <DropdownMenuItem className="hover:bg-accent hover:text-accent-foreground cursor-pointer transition-colors duration-200 rounded-md px-2 py-1.5">
                  <button 
                    className="w-full text-left text-sm text-red-600 hover:text-red-700"
                    onClick={handleLogout}
                  >
                    Sign out
                  </button>
                </DropdownMenuItem>
                
                <DropdownMenuItem className="hover:bg-accent hover:text-accent-foreground cursor-pointer transition-colors duration-200 rounded-md px-2 py-1.5">
                  <button className="w-full text-sm text-left" >Delete Account</button>
                </DropdownMenuItem>
              
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <AlertDialog open={!!pendingDeleteId} onOpenChange={(open) => !open && setPendingDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="text-primary-foreground">Delete this project?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the chat session and its messages. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="text-primary-foreground" disabled={isDeleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} disabled={isDeleting}>
              {isDeleting ? "Deleting…" : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
     
      <AlertDialog open={confirmAccountOpen} onOpenChange={(open) => !open && !isDeletingAccount && setConfirmAccountOpen(open)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="text-primary-foreground">Delete your account?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete your account and all associated data. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="text-primary-foreground"disabled={isDeletingAccount}>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDeleteAccount} disabled={isDeletingAccount}>
              {isDeletingAccount ? "Deleting…" : "Delete account"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog> 
    </Sidebar>
  )
}