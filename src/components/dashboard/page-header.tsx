interface PageHeaderProps {
  title: string;
  summary?: string | null;
  generatedAt?: string;
}

export function PageHeader({ title, summary, generatedAt }: PageHeaderProps) {
  return (
    <header className="flex flex-col gap-1">
      <h1 className="text-xl font-semibold">{title}</h1>
      {summary ? <p className="text-sm text-muted-foreground">{summary}</p> : null}
      {generatedAt ? (
        <p className="text-xs text-muted-foreground">
          마지막 갱신: {new Date(generatedAt).toLocaleString("ko-KR")}
        </p>
      ) : null}
    </header>
  );
}
