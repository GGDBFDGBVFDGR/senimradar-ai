import { Link } from "react-router-dom";

import { useI18n } from "../i18n/LanguageProvider.tsx";
import { PageHeader } from "../components/ui/PageHeader.tsx";

export function NotFoundPage() {
  const { messages } = useI18n();
  return (
    <div className="space-y-6">
      <PageHeader title={messages.notFound.title} description={messages.notFound.body} />
      <Link to="/" className="inline-flex rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-bold text-navy-950">
        {messages.notFound.home}
      </Link>
    </div>
  );
}
