"use client";

import { useEffect, useState } from "react";
import {
  Table2,
  Download,
  Search,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  FileWarning,
  CheckCircle2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getFeatures, getFeaturesDownloadUrl, getIssues } from "@/lib/api";
import type { FeaturesResponse } from "@/lib/types";

export default function ResultsPage() {
  const [data, setData] = useState<FeaturesResponse | null>(null);
  const [issues, setIssues] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(50);
  const [search, setSearch] = useState("");
  const [sortCol, setSortCol] = useState("");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [searchInput, setSearchInput] = useState("");

  const loadData = () => {
    setLoading(true);
    setError("");
    getFeatures({ page, per_page: perPage, search, sort: sortCol, order: sortOrder })
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  const loadIssues = () => {
    getIssues()
      .then((res) => setIssues(res.issues))
      .catch(() => setIssues(null));
  };

  useEffect(() => {
    loadData();
    loadIssues();
  }, [page, perPage, search, sortCol, sortOrder]);

  const handleSearch = () => {
    setSearch(searchInput);
    setPage(1);
  };

  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortCol(col);
      setSortOrder("asc");
    }
    setPage(1);
  };

  const totalPages = data?.total_pages ?? 1;
  const canPrev = page > 1;
  const canNext = page < totalPages;

  if (loading && !data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Results</h1>
        <Card>
          <CardContent className="flex items-center justify-center py-16">
            <p className="text-muted-foreground">Loading results...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold tracking-tight">Results</h1>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Table2 className="h-12 w-12 text-muted-foreground/30 mb-4" />
            <p className="text-muted-foreground mb-2">No results available</p>
            <p className="text-sm text-muted-foreground max-w-md text-center">
              {error}
            </p>
            <p className="text-xs text-muted-foreground mt-4">
              Run the pipeline to generate feature extraction results
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Results</h1>
          <p className="text-muted-foreground">
            Extracted radiomic features from pipeline runs
          </p>
        </div>
        {data && (
          <a href={getFeaturesDownloadUrl()} download>
            <Button>
              <Download className="mr-2 h-4 w-4" />
              Download CSV
            </Button>
          </a>
        )}
      </div>

      {/* Issues Warning */}
      {issues && (
        <Card className="border-amber-500/50 bg-amber-500/5">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <FileWarning className="h-4 w-4 text-amber-500" />
              Processing Issues
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="text-xs whitespace-pre-wrap font-mono">{issues}</pre>
          </CardContent>
        </Card>
      )}

      {/* Success Badge */}
      {data && !issues && (
        <Card className="border-emerald-500/50 bg-emerald-500/5">
          <CardContent className="flex items-center gap-3 pt-6">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            <div>
              <p className="font-semibold">Processing Complete</p>
              <p className="text-sm text-muted-foreground">
                {data.total_rows} features extracted successfully
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search & Controls */}
      {data && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4 flex-wrap">
              <div className="flex-1 min-w-[200px]">
                <div className="flex gap-2">
                  <Input
                    placeholder="Search features..."
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSearch();
                    }}
                  />
                  <Button onClick={handleSearch} variant="secondary">
                    <Search className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">Rows:</span>
                <Select
                  value={String(perPage)}
                  onValueChange={(val) => {
                    setPerPage(parseInt(val));
                    setPage(1);
                  }}
                >
                  <SelectTrigger className="w-20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="25">25</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="200">200</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Table */}
      {data && (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="border-b bg-muted/50">
                  <tr>
                    {data.columns.map((col) => (
                      <th
                        key={col}
                        className="px-4 py-3 text-left font-medium cursor-pointer hover:bg-muted transition-colors"
                        onClick={() => handleSort(col)}
                      >
                        <div className="flex items-center gap-1">
                          {col}
                          {sortCol === col && (
                            <span className="text-xs">
                              {sortOrder === "asc" ? "↑" : "↓"}
                            </span>
                          )}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.rows.length === 0 ? (
                    <tr>
                      <td
                        colSpan={data.columns.length}
                        className="px-4 py-8 text-center text-muted-foreground"
                      >
                        No results found
                      </td>
                    </tr>
                  ) : (
                    data.rows.map((row, idx) => (
                      <tr
                        key={idx}
                        className="border-b last:border-0 hover:bg-muted/50 transition-colors"
                      >
                        {data.columns.map((col) => (
                          <td key={col} className="px-4 py-3">
                            {typeof row[col] === "number"
                              ? (row[col] as number).toLocaleString(undefined, {
                                  maximumFractionDigits: 6,
                                })
                              : String(row[col] ?? "")}
                          </td>
                        ))}
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Page {page} of {totalPages} ({data.total_rows} total rows)
              </p>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(1)}
                  disabled={!canPrev}
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={!canPrev}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="px-4 text-sm">{page}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={!canNext}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(totalPages)}
                  disabled={!canNext}
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
