type Props = {
  badge: string;
  title: string;
  subtitle: string;
};

export function PageHeader({ badge, title, subtitle }: Props) {
  return (
    <header className="text-center sm:text-left">
      <span className="ui-badge">{badge}</span>
      <h1 className="mt-4 text-3xl font-bold tracking-tight text-white sm:text-4xl">{title}</h1>
      <p className="mx-auto mt-3 max-w-2xl text-base leading-relaxed text-slate-400 sm:mx-0">{subtitle}</p>
    </header>
  );
}
