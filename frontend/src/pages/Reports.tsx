import { useState, useRef } from "react";
import { Download, Upload, FileText, FileSpreadsheet, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { exportApi, uploadApi, aiApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { ImportSummary, AIResponse } from "@/types";

type ExportType = "sales" | "customers" | "inventory" | "report";
type UploadType = "orders" | "customers" | "products" | "inventory";

export default function Reports() {
  const [exporting, setExporting] = useState<ExportType | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadType, setUploadType] = useState<UploadType>("orders");
  const [importResult, setImportResult] = useState<ImportSummary | null>(null);
  const [aiReport, setAiReport] = useState<AIResponse | null>(null);
  const [generating, setGenerating] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExport = async (type: ExportType) => {
    setExporting(type);
    try {
      if (type === "sales") {
        const res = await exportApi.salesCSV();
        downloadBlob(new Blob([res.data]), "sales_report.csv");
      } else if (type === "customers") {
        const res = await exportApi.customersCSV();
        downloadBlob(new Blob([res.data]), "customers_report.csv");
      } else if (type === "inventory") {
        const res = await exportApi.inventoryCSV();
        downloadBlob(new Blob([res.data]), "inventory_report.csv");
      } else {
        const res = await exportApi.businessReportPDF();
        downloadBlob(new Blob([res.data]), "business_report.pdf");
      }
    } catch (e) {
      console.error("Export failed:", e);
    } finally {
      setExporting(null);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setImportResult(null);
    try {
      const fns: Record<UploadType, (f: File) => Promise<{ data: ImportSummary }>> = {
        orders: uploadApi.uploadOrders,
        customers: uploadApi.uploadCustomers,
        products: uploadApi.uploadProducts,
        inventory: uploadApi.uploadInventory,
      };
      const res = await fns[uploadType](file);
      setImportResult(res.data);
    } catch (e) {
      console.error("Upload failed:", e);
      setImportResult({ total_rows: 0, success_rows: 0, failed_rows: 0, duplicate_rows: 0, errors: ["Upload failed. Please check the file format."] });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const handleGenerateAIReport = async () => {
    setGenerating(true);
    setAiReport(null);
    try {
      const res = await aiApi.generateReport("weekly");
      setAiReport(res.data);
    } catch {
      setAiReport({ short_answer: "Failed to generate report. Please try again.", data_evidence: [], reasoning: "", suggested_actions: [], confidence: "low" });
    } finally {
      setGenerating(false);
    }
  };

  const exportCards = [
    { type: "sales" as ExportType, title: "Sales Report", desc: "All orders with customer and product details", icon: FileSpreadsheet, format: "CSV" },
    { type: "customers" as ExportType, title: "Customer Report", desc: "Complete customer directory with spending data", icon: FileSpreadsheet, format: "CSV" },
    { type: "inventory" as ExportType, title: "Inventory Report", desc: "Product stock levels and reorder status", icon: FileSpreadsheet, format: "CSV" },
    { type: "report" as ExportType, title: "Business Report", desc: "Executive summary with key metrics", icon: FileText, format: "PDF" },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold tracking-tight">Reports & Export</h2>

      {/* Export Section */}
      <div>
        <h3 className="mb-3 text-lg font-medium">Export Data</h3>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {exportCards.map((card) => (
            <Card key={card.type}>
              <CardContent className="p-4">
                <card.icon className="mb-2 h-8 w-8 text-muted-foreground" />
                <h4 className="font-medium">{card.title}</h4>
                <p className="mt-1 text-xs text-muted-foreground">{card.desc}</p>
                <div className="mt-3 flex items-center justify-between">
                  <Badge variant="outline">{card.format}</Badge>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleExport(card.type)}
                    disabled={exporting === card.type}
                  >
                    {exporting === card.type ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="mr-1 h-4 w-4" />}
                    Export
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* AI Report */}
      <div>
        <h3 className="mb-3 text-lg font-medium">AI Business Report</h3>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-medium">Generate AI-Powered Report</h4>
                <p className="text-sm text-muted-foreground">
                  Uses AI to analyze your business data and generate a comprehensive weekly report with insights and recommendations.
                </p>
              </div>
              <Button onClick={handleGenerateAIReport} disabled={generating}>
                {generating ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Generating...</> : <><FileText className="mr-2 h-4 w-4" />Generate Report</>}
              </Button>
            </div>
            {aiReport && (
              <div className="mt-4 rounded-lg border p-4">
                <h5 className="font-medium">{aiReport.short_answer}</h5>
                {aiReport.data_evidence.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-semibold text-muted-foreground">Data Evidence:</p>
                    <ul className="mt-1 list-inside list-disc text-sm">{aiReport.data_evidence.map((e, i) => <li key={i}>{e}</li>)}</ul>
                  </div>
                )}
                {aiReport.reasoning && <div className="mt-2"><p className="text-xs font-semibold text-muted-foreground">Reasoning:</p><p className="text-sm">{aiReport.reasoning}</p></div>}
                {aiReport.suggested_actions.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-semibold text-muted-foreground">Recommended Actions:</p>
                    <ul className="mt-1 list-inside list-disc text-sm">{aiReport.suggested_actions.map((a, i) => <li key={i}>{a}</li>)}</ul>
                  </div>
                )}
                <div className="mt-2"><Badge variant={aiReport.confidence === "high" ? "default" : aiReport.confidence === "medium" ? "secondary" : "destructive"}>Confidence: {aiReport.confidence}</Badge></div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Upload Section */}
      <div>
        <h3 className="mb-3 text-lg font-medium">Import CSV Data</h3>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-end gap-3">
              <div>
                <label className="text-xs font-medium text-muted-foreground">Data Type</label>
                <select
                  className="block h-9 rounded-md border bg-background px-3 text-sm"
                  value={uploadType}
                  onChange={(e) => setUploadType(e.target.value as UploadType)}
                >
                  <option value="orders">Orders</option>
                  <option value="customers">Customers</option>
                  <option value="products">Products</option>
                  <option value="inventory">Inventory</option>
                </select>
              </div>
              <div className="flex-1">
                <label className="text-xs font-medium text-muted-foreground">CSV File</label>
                <input
                  ref={fileRef}
                  type="file"
                  accept=".csv"
                  onChange={handleUpload}
                  className="block h-9 w-full rounded-md border bg-background px-3 text-sm file:mr-3 file:border-0 file:bg-primary/10 file:px-2 file:py-1 file:text-sm file:font-medium"
                  disabled={uploading}
                />
              </div>
            </div>

            {uploading && (
              <div className="mt-4 flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Processing file...
              </div>
            )}

            {importResult && (
              <div className="mt-4 rounded-lg border p-4">
                <div className="mb-3 flex items-center gap-2">
                  {importResult.failed_rows === 0 && importResult.errors.length === 0 ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-amber-500" />
                  )}
                  <span className="font-medium">Import Complete</span>
                </div>
                <div className="grid grid-cols-4 gap-3 text-center">
                  <div className="rounded bg-gray-50 p-2">
                    <p className="text-lg font-bold">{importResult.total_rows}</p>
                    <p className="text-xs text-muted-foreground">Total Rows</p>
                  </div>
                  <div className="rounded bg-green-50 p-2">
                    <p className="text-lg font-bold text-green-600">{importResult.success_rows}</p>
                    <p className="text-xs text-muted-foreground">Successful</p>
                  </div>
                  <div className="rounded bg-red-50 p-2">
                    <p className="text-lg font-bold text-red-600">{importResult.failed_rows}</p>
                    <p className="text-xs text-muted-foreground">Failed</p>
                  </div>
                  <div className="rounded bg-yellow-50 p-2">
                    <p className="text-lg font-bold text-yellow-600">{importResult.duplicate_rows}</p>
                    <p className="text-xs text-muted-foreground">Duplicates</p>
                  </div>
                </div>
                {importResult.errors.length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-muted-foreground">Errors:</p>
                    <ul className="mt-1 max-h-32 overflow-y-auto text-xs text-red-600">
                      {importResult.errors.map((err, i) => <li key={i}>{err}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
