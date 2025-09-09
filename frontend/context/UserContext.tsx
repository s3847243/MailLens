"use client"
import { createContext, useContext, useMemo, useState } from "react";
import { User } from "@/types";

type UserCtx = {
  user: User | null;
  setUser: (u: User | null) => void;
};

const Ctx = createContext<UserCtx | undefined>(undefined);


export function UserProvider({
  initialUser,
  children,
}: {
  initialUser: User | null;
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<User | null>(initialUser);
  const value = useMemo(() => ({ user, setUser }), [user]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useUser() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useUser must be used within <UserProvider>");
  return ctx;
}
