/**
 * PDFUploadDialog - Upload portfolio PDF and get session ID
 */

import { useState, type ChangeEvent } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Upload, FileText, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { uploadPortfolio } from "@/services/mcp-tools";

interface PDFUploadDialogProps {
  onUploadSuccess: (sessionId: string, filename: string) => void;
}

export function PDFUploadDialog({ onUploadSuccess }: PDFUploadDialogProps) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState<string>("");

  function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      // Validate file type
      if (selectedFile.type !== "application/pdf") {
        setErrorMessage("Please select a PDF file");
        setUploadStatus("error");
        return;
      }

      // Validate file size (max 10MB)
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (selectedFile.size > maxSize) {
        setErrorMessage("File size must be less than 10MB");
        setUploadStatus("error");
        return;
      }

      setFile(selectedFile);
      setUploadStatus("idle");
      setErrorMessage("");
    }
  }

  async function handleUpload() {
    if (!file) return;

    setIsUploading(true);
    setUploadStatus("idle");
    setErrorMessage("");

    try {
      // Convert PDF to base64
      const base64 = await convertFileToBase64(file);

      // Call MCP upload_portfolio tool
      const result = await uploadPortfolio(base64, file.name);

      setUploadStatus("success");
      setIsUploading(false);

      // Wait a moment to show success message, then close and callback
      setTimeout(() => {
        setOpen(false);
        onUploadSuccess(result.session_id, file.name);

        // Reset state
        setFile(null);
        setUploadStatus("idle");
      }, 1500);
    } catch (error) {
      setUploadStatus("error");
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to upload PDF",
      );
      setIsUploading(false);
    }
  }

  function convertFileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result as string;
        // Remove data:application/pdf;base64, prefix
        const base64Data = base64.split(",")[1];
        resolve(base64Data);
      };
      reader.onerror = (error) => reject(error);
    });
  }

  function handleOpenChange(isOpen: boolean) {
    // Don't allow closing while uploading
    if (isUploading) return;

    setOpen(isOpen);

    // Reset state when closing
    if (!isOpen) {
      setFile(null);
      setUploadStatus("idle");
      setErrorMessage("");
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Upload className="mr-2 h-4 w-4" />
          Upload PDF
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Upload Portfolio PDF</DialogTitle>
          <DialogDescription>
            Upload your portfolio valuation PDF to analyze your investments.
            Supports WealthPoint, Pictet, UBS, and other bank formats.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 py-4">
          {/* File Input */}
          <div className="grid gap-2">
            <Label htmlFor="pdf-file">Portfolio PDF</Label>
            <Input
              id="pdf-file"
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileChange}
              disabled={isUploading}
            />
            <p className="text-xs text-muted-foreground">
              Maximum file size: 10MB
            </p>
          </div>

          {/* Selected File Info */}
          {file && uploadStatus === "idle" && (
            <div className="flex items-center gap-2 rounded-md border p-3">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <div className="flex-1">
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
          )}

          {/* Success Message */}
          {uploadStatus === "success" && (
            <Alert className="border-green-500 bg-green-50 dark:bg-green-950">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800 dark:text-green-200">
                Portfolio uploaded successfully! Starting analysis...
              </AlertDescription>
            </Alert>
          )}

          {/* Error Message */}
          {uploadStatus === "error" && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button onClick={handleUpload} disabled={!file || isUploading}>
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload & Analyze
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
