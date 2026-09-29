import { createNavigation } from "next-intl/navigation";
import { routing } from "./routing";

// Wrappers de Link/useRouter/redirect cientes do locale (T012).
export const { Link, redirect, usePathname, useRouter } =
  createNavigation(routing);
