"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

function TopLabel() {
  const pathname = usePathname();
  if (pathname.startsWith("/bookshelf")) return "Bookshelf";
  if (pathname.startsWith("/projects")) return "Projects";
  if (pathname.startsWith("/sessions")) return "Sessions";
  if (pathname.startsWith("/artifacts")) return "Artifacts";
  return "Dashboard";
}

/** Sticky top bar: sidebar trigger, a section breadcrumb, and the theme toggle. */
export function Topbar() {
  const label = TopLabel();
  return (
    <header className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-2 border-b bg-background/80 px-4 backdrop-blur">
      <SidebarTrigger className="-ml-1" />
      <Separator orientation="vertical" className="mr-1 h-4" />
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem className="hidden sm:block">
            <BreadcrumbLink asChild>
              <Link href="/">Agent Orchestrator</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <span className="hidden text-muted-foreground sm:block">/</span>
          <BreadcrumbItem>
            <BreadcrumbPage>{label}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="ml-auto">
        <ThemeToggle />
      </div>
    </header>
  );
}
