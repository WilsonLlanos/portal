import { Certifications } from "@/components/sections/Certifications";
import { Hero } from "@/components/sections/Hero";
import { Projects } from "@/components/sections/Projects";
import { Summary } from "@/components/sections/Summary";
import { Timeline } from "@/components/sections/Timeline";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { Header } from "@/components/ui/Header";
import { routing } from "@/i18n/routing";
import { getProfile } from "@/lib/content/loader";
import type { Locale } from "@/lib/content/schema";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

// T028/T034/T057/T064: composição das seções: hero, resumo, trajetória,
// projetos e certificações. Os contatos ficam no hero, abaixo da foto, e o chat é um widget
// flutuante, independente das seções.
export default async function Home({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const loc = locale as Locale;
  const profile = getProfile(loc);

  return (
    <>
      <Header />
      <main className="space-y-6 px-3 py-6 sm:px-6 md:space-y-8">
        <Hero locale={loc} />
        <Summary locale={loc} />
        <Timeline locale={loc} />
        <Projects locale={loc} />
        <Certifications locale={loc} />
      </main>
      <ChatPanel contactHref={profile.links.whatsapp} cvHref={`/cv/cv-${loc}.pdf`} />
    </>
  );
}
