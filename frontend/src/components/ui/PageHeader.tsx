export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description: string;
}) {
  return (
    <header className="max-w-3xl">
      {eyebrow ? (
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">{eyebrow}</p>
      ) : null}
      <h1 className="mt-2 font-display text-3xl font-bold tracking-tight text-ink sm:text-4xl">{title}</h1>
      <p className="mt-3 text-base leading-7 text-muted sm:text-lg">{description}</p>
    </header>
  );
}
