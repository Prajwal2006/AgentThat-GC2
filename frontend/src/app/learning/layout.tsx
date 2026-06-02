import { Sidebar } from "@/components/sidebar";
import { Header } from "@/components/header";

export default function LearningLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 lg:ml-0">
        <Header />
        {children}
      </main>
    </div>
  );
}
