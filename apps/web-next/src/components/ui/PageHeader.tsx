import Link from "next/link";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: React.ReactNode;
  backHref?: string;
  backLabel?: string;
  actions?: React.ReactNode;
};

export function PageHeader({
  eyebrow,
  title,
  description,
  backHref,
  backLabel = "返回",
  actions,
}: PageHeaderProps) {
  return (
    <header className="mb-10">
      {backHref ? (
        <Link href={backHref} className="link-back mb-4 inline-block">
          ← {backLabel}
        </Link>
      ) : null}
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div className="max-w-2xl">
          {eyebrow ? <p className="ui-label mb-2">{eyebrow}</p> : null}
          <h1 className="display-title text-3xl sm:text-4xl">{title}</h1>
          {description ? (
            <p className="mt-3 text-[0.95rem] leading-relaxed text-ink-muted">{description}</p>
          ) : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
      </div>
    </header>
  );
}
