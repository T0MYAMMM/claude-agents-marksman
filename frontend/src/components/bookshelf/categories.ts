import {
  BookMarked,
  BookOpen,
  Compass,
  GraduationCap,
  Network,
  Scale,
  type LucideIcon,
} from "lucide-react";

import type { BookCategory } from "@/types";

export interface CategoryMeta {
  key: BookCategory;
  label: string;
  icon: LucideIcon;
}

/** The 6 fixed categories, in their canonical shelf order. */
export const CATEGORIES: CategoryMeta[] = [
  { key: "overview", label: "Overview", icon: BookOpen },
  { key: "architecture", label: "Architecture", icon: Network },
  { key: "guides", label: "Guides", icon: Compass },
  { key: "tutorials", label: "Tutorials", icon: GraduationCap },
  { key: "reference", label: "Reference", icon: BookMarked },
  { key: "rules", label: "Rules", icon: Scale },
];

/** Strip a trailing .md extension for display. */
export function bookTitle(fileName: string): string {
  return fileName.replace(/\.md$/i, "");
}
