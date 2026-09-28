import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CasesSection } from "@/types/page";

interface CaseCardsProps {
  section: CasesSection;
}

export function CaseCards({ section }: CaseCardsProps) {
  return (
    <section className="flex flex-col gap-3">
      <h2 className="text-base font-semibold">{section.title}</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {section.cards.map((card) => (
          <Card key={card.id}>
            <CardHeader>
              <div className="flex items-start justify-between gap-2">
                <div className="flex flex-col gap-0.5">
                  <CardTitle>{card.title}</CardTitle>
                  {card.subtitle ? <p className="text-xs text-muted-foreground">{card.subtitle}</p> : null}
                </div>
                {card.badge ? <Badge variant="secondary">{card.badge}</Badge> : null}
              </div>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <p className="text-sm text-foreground">{card.body}</p>
              {card.metrics.length > 0 ? (
                <dl className="grid grid-cols-2 gap-2">
                  {card.metrics.map((metric) => (
                    <div key={metric.label} className="flex flex-col">
                      <dt className="text-xs text-muted-foreground">{metric.label}</dt>
                      <dd className="text-sm font-medium">{metric.value}</dd>
                    </div>
                  ))}
                </dl>
              ) : null}
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
