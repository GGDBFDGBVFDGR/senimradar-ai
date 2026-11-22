import type { ReactNode } from "react";

import { Card } from "./Card.tsx";
import { PageHeader } from "./PageHeader.tsx";
import { StageBanner } from "./StageBanner.tsx";

export function FutureModule({
  title,
  description,
  stage,
  tone,
  points,
  children,
}: {
  title: string;
  description: string;
  stage: number;
  tone: "planned" | "unavailable" | "disabled";
  points: readonly string[];
  children?: ReactNode;
}) {
  return (
    <div className="space-y-6">
      <PageHeader title={title} description={description} />
      <StageBanner stage={stage} tone={tone} />
      <Card>
        <ul className="space-y-3">
          {points.map((point) => (
            <li key={point} className="flex gap-3 text-sm leading-6 text-muted">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-300" />
              <span>{point}</span>
            </li>
          ))}
        </ul>
        {children ? <div className="mt-6 border-t border-line pt-5">{children}</div> : null}
      </Card>
    </div>
  );
}
