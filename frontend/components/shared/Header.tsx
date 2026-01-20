"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Icon } from "./Icon";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/" },
  { name: "Meetings", href: "/meetings" },
  { name: "Tasks", href: "/tasks" },
  { name: "Analytics", href: "/analytics" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between whitespace-nowrap border-b border-border bg-white/80 dark:bg-card/80 backdrop-blur-md px-10 py-3">
      <div className="flex items-center gap-8">
        <Link href="/" className="flex items-center gap-4 text-primary">
          <div className="size-6 bg-primary rounded-lg flex items-center justify-center text-white">
            <Icon name="auto_awesome" className="text-lg" />
          </div>
          <h2 className="text-slate-900 dark:text-white text-xl font-extrabold leading-tight tracking-tight">
            TaskLedger
          </h2>
        </Link>
        
        <div className="flex flex-col min-w-40 h-10 max-w-64">
          <div className="relative flex w-full h-full items-center">
            <Icon 
              name="search" 
              className="absolute left-4 text-[20px] text-muted-foreground" 
            />
            <Input
              className="h-full w-full rounded-lg bg-slate-100 dark:bg-slate-800 border-none pl-12 text-base placeholder:text-slate-500"
              placeholder="Search transcripts..."
            />
          </div>
        </div>
      </div>

      <div className="flex flex-1 justify-end gap-6 items-center">
        <nav className="flex items-center gap-6">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "text-base font-medium leading-normal transition-colors hover:text-primary",
                  isActive 
                    ? "text-primary font-bold border-b-2 border-primary pb-1" 
                    : "text-slate-600 dark:text-slate-400"
                )}
              >
                {item.name}
              </Link>
            );
          })}
        </nav>
        
        <div className="h-6 w-[1px] bg-slate-200 dark:bg-slate-700" />
        
        <Button 
          asChild
          className="min-w-[120px] gap-2 bg-primary text-white text-base font-bold shadow-lg shadow-primary/20 hover:bg-primary/90"
        >
          <Link href="/meetings/new">
            <Icon name="add" className="text-sm" />
            <span>New Meeting</span>
          </Link>
        </Button>
        
        <div 
          className="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-9 border border-slate-200 dark:border-slate-700 bg-gradient-to-br from-primary/20 to-primary/40"
          aria-label="User profile"
        />
      </div>
    </header>
  );
}
