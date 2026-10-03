import Logo from "@/components/tt/Logo";

export default function AuthLayout({ title, subtitle, children, footer, wide }) {
  return (
    <div className="hero-glow flex min-h-screen flex-col">
      <header className="px-6 py-5">
        <Logo />
      </header>
      <main className="flex flex-1 items-center justify-center px-4 pb-12">
        <div className={`card-surface w-full p-6 sm:p-8 ${wide ? "max-w-xl" : "max-w-md"}`}>
          {title && <h1 className="text-2xl font-bold sm:text-3xl">{title}</h1>}
          {subtitle && <p className="mt-1.5 text-sm text-muted-foreground">{subtitle}</p>}
          <div className="mt-6">{children}</div>
          {footer && <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>}
        </div>
      </main>
    </div>
  );
}
