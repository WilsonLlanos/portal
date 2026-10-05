import { Certifications } from "@/components/sections/Certifications";
import { Contact } from "@/components/sections/Contact";
import { Hero } from "@/components/sections/Hero";
import { Projects } from "@/components/sections/Projects";
import { Summary } from "@/components/sections/Summary";
import { Timeline } from "@/components/sections/Timeline";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { Header } from "@/components/ui/Header";
import { routing } from "@/i18n/routing";
import type { Locale } from "@/lib/content/schema";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

// T028/T034/T057/T064: composição das seções, na ordem definida em
// spec.md § Seções: hero, resumo, trajetória, projetos, certificações,
// chat, contato.
export default async function Home({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const loc = locale as Locale;

  return (
    <>
      <Header />
      <main className="space-y-6 px-3 py-6 sm:px-6 md:space-y-8">
        <Hero locale={loc} />
        <Summary locale={loc} />
        <Timeline locale={loc} />
        <Projects locale={loc} />
        <Certifications locale={loc} />
        <ChatPanel />
        <Contact locale={loc} />
      </main>
    </>
  );
}
