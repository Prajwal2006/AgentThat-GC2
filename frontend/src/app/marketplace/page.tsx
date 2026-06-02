"use client";

import { useState } from "react";
import {
  Search,
  Star,
  Download,
  Filter,
  MessageSquare,
  TrendingUp,
  Users,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AppLayout } from "@/components/app-layout";
import { marketplaceItems } from "@/lib/mock-data";
import { MarketplaceItem, apiPost, useApiResource } from "@/lib/api";

const iconMap: Record<string, React.ReactNode> = {
  MessageSquare: <MessageSquare className="w-8 h-8" />,
  TrendingUp: <TrendingUp className="w-8 h-8" />,
  Users: <Users className="w-8 h-8" />,
  FileText: <FileText className="w-8 h-8" />,
};

export default function MarketplacePage() {
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [query, setQuery] = useState("");
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const { data: items, loading, error, setData } = useApiResource<MarketplaceItem[]>(
    "/v1/marketplace",
    marketplaceItems
  );

  const installItem = async (itemId: string) => {
    try {
      const result = await apiPost<{ status: string; item: MarketplaceItem }>(
        `/v1/marketplace/${itemId}/install`,
        {}
      );
      setData((current) =>
        current.map((item) => (item.id === itemId ? result.item : item))
      );
      setStatusMessage(`Installed ${result.item.name}.`);
    } catch (err) {
      setStatusMessage(err instanceof Error ? err.message : "Could not install item.");
    }
  };

  const categories = [
    { id: "all", name: "All" },
    { id: "support", name: "Support" },
    { id: "sales", name: "Sales" },
    { id: "hr", name: "HR" },
    { id: "marketing", name: "Marketing" },
  ];
  const filteredItems = items.filter((item) => {
    const matchesCategory =
      selectedCategory === "all" || item.category.toLowerCase() === selectedCategory;
    const normalizedQuery = query.trim().toLowerCase();
    const matchesQuery =
      !normalizedQuery ||
      item.name.toLowerCase().includes(normalizedQuery) ||
      item.description.toLowerCase().includes(normalizedQuery);
    return matchesCategory && matchesQuery;
  });

  return (
    <AppLayout>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">AI Marketplace</h1>
          <p className="text-muted-foreground">
            Discover and install pre-built agents, workflows, and integrations
          </p>
        </div>
        <Badge variant={error ? "destructive" : loading ? "info" : "success"}>
          {error ? "Backend offline" : loading ? "Syncing" : "Live catalog"}
        </Badge>
      </div>
      {statusMessage && <Badge variant="info">{statusMessage}</Badge>}

      {/* Search and Filters */}
      <div className="space-y-4">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search agents, workflows..."
              className="pl-10"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
          <Button variant="outline" className="gap-2">
            <Filter className="w-4 h-4" />
            Filter
          </Button>
        </div>

        {/* Category Filter */}
        <div className="flex gap-2 flex-wrap">
          {categories.map((cat) => (
            <Button
              key={cat.id}
              variant={selectedCategory === cat.id ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(cat.id)}
            >
              {cat.name}
            </Button>
          ))}
        </div>
      </div>

      {/* Marketplace Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        {filteredItems.map((item) => (
          <Card
            key={item.id}
            className="hover:border-accent/50 transition-all hover:shadow-lg cursor-pointer flex flex-col"
          >
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4 flex-1">
                  <div className="p-3 rounded-lg bg-accent/10 border border-accent/20">
                    {iconMap[item.icon]}
                  </div>
                  <div className="flex-1">
                    <CardTitle className="text-lg">{item.name}</CardTitle>
                    <CardDescription className="text-xs mt-1">
                      by {item.creator}
                    </CardDescription>
                  </div>
                </div>
              </div>
            </CardHeader>

            <CardContent className="flex-1 space-y-4">
              <p className="text-sm text-muted-foreground">
                {item.description}
              </p>

              <div className="flex items-center gap-2">
                <div className="flex items-center">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      className={`w-4 h-4 ${
                        i < Math.floor(item.rating)
                          ? "fill-accent text-accent"
                          : "text-muted"
                      }`}
                    />
                  ))}
                </div>
                <span className="text-xs text-muted-foreground">
                  {item.rating} ({item.installs} installs)
                </span>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-border">
                <Badge variant="outline">{item.category}</Badge>
                <Button className="gap-2" size="sm" onClick={() => installItem(item.id)}>
                  <Download className="w-4 h-4" />
                  Install
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Featured Section */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">Featured Collections</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { name: "Sales & Revenue", count: 12 },
            { name: "Customer Success", count: 8 },
            { name: "Operations", count: 15 },
          ].map((collection, idx) => (
            <Card key={idx} className="hover:border-accent/50 transition-colors cursor-pointer">
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-2">{collection.name}</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {collection.count} items
                </p>
                <Button variant="outline" className="w-full">
                  Explore
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
