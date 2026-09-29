import { hasLocale, NextIntlClientProvider } from "next-intl";
import { notFound } from "next/navigation";
import type { Metadata } from "next";
import "../globals.css";
import { routing } from "@/i18n/routing";
import { ThemeProvider } from "@/components/ui/ThemeProvider";
import { getProfile } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

// FR-012: metadados de SEO/Open Graph por idioma.
export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const profile = getProfile(locale as Locale);

  const title = `${profile.name} — ${profile.headline}`;
  const description = profile.tagline;
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";

  return {
    title,
    description,
    metadataBase: new URL(siteUrl),
    openGraph: {
      title,
      description,
      locale,
      images: [{ url: profile.photo.src }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
    },
    alternates: {
      languages: {
        "pt-BR": "/pt-BR",
        en: "/en",
      },
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) {
    notFound();
  }

  return (
    <html lang={locale} suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <NextIntlClientProvider>{children}</NextIntlClientProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
