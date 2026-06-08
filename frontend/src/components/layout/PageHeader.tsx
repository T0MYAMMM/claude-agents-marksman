import * as React from "react";
import Link from "next/link";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

export interface Crumb {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  /** Breadcrumb trail; the last entry renders as the current page. */
  crumbs: Crumb[];
  title: string;
  description?: string | null;
  /** Right-aligned content (badges, actions). */
  actions?: React.ReactNode;
}

/**
 * Server-rendered page header: breadcrumb row + display title + optional
 * description and right-aligned actions. Rendered at the top of each page's
 * content (the Topbar provides only the sidebar trigger + theme toggle).
 */
export function PageHeader({
  crumbs,
  title,
  description,
  actions,
}: PageHeaderProps) {
  return (
    <div className="mb-6 space-y-4">
      <Breadcrumb>
        <BreadcrumbList>
          {crumbs.map((crumb, i) => {
            const isLast = i === crumbs.length - 1;
            return (
              <React.Fragment key={`${crumb.label}-${i}`}>
                <BreadcrumbItem>
                  {isLast || !crumb.href ? (
                    <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                  ) : (
                    <BreadcrumbLink asChild>
                      <Link href={crumb.href}>{crumb.label}</Link>
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
                {!isLast && <BreadcrumbSeparator />}
              </React.Fragment>
            );
          })}
        </BreadcrumbList>
      </Breadcrumb>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <h1 className="font-display text-2xl md:text-3xl">{title}</h1>
          {description && (
            <p className="max-w-2xl text-sm text-muted-foreground md:text-base">
              {description}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
}
