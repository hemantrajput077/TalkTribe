import Navbar, { MobileNav } from "@/components/tt/Navbar";

export default function AppLayout({ children }) {
  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 sm:py-10">{children}</main>
      <MobileNav />
    </div>
  );
}
