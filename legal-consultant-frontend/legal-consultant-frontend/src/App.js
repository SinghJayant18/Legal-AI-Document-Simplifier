import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';

// Placeholder for icons (replace with actual icon components or SVGs)
const ScaleIcon = () => <svg className="w-16 h-16 text-blue-500" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7h20zM2 17h20v5H2z" /></svg>;
const DocumentIcon = () => <svg className="w-6 h-6 text-blue-500" viewBox="0 0 24 24" fill="currentColor"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" /></svg>;
const UploadIcon = () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M3 16v5h18v-5H3zm9-12l6 6H6l6-6z" /></svg>;
const CopyIcon = () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M16 1H4a2 2 0 00-2 2v14h2V3h12V1zm3 4H8a2 2 0 00-2 2v14a2 2 0 002 2h11a2 2 0 002-2V7a2 2 0 00-2-2z" /></svg>;
const ClearIcon = () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M6 18L18 6M6 6l12 12" /></svg>;
const LoadingIcon = () => <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="currentColor"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2" /></svg>;
const CheckIcon = () => <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M20 6L9 17l-5-5" /></svg>;

// Placeholder for useToast hook (simplified)
const useToast = () => ({
  toast: ({ title, description, variant }) => {
    alert(`${title}: ${description}${variant === 'destructive' ? ' (Error)' : ''}`);
  }
});

// Placeholder for Button and Textarea components
const Button = ({ children, onClick, disabled, variant = 'default', className }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`px-4 py-2 rounded-lg ${variant === 'ghost' ? 'bg-transparent text-gray-700 hover:bg-gray-100' : 'bg-blue-500 text-white hover:bg-blue-600'} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
  >
    {children}
  </button>
);

const Textarea = ({ id, value, onChange, placeholder, disabled, className }) => (
  <textarea
    id={id}
    value={value}
    onChange={onChange}
    placeholder={placeholder}
    disabled={disabled}
    className={`w-full p-3 border rounded-lg bg-white text-gray-900 ${disabled ? 'opacity-50' : ''} ${className}`}
  />
);

const BACKEND_URL = "http://127.0.0.1:8000";

export default function LegalAIConsultant() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [references, setReferences] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadingPct, setUploadingPct] = useState(null);
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  const samples = [
    "What is the punishment under IPC 302?",
    "What are the essentials of defamation (IPC 499)?",
    "When is bail likely for theft under CrPC?",
    "Steps to file an FIR for assault?",
    "Rights of accused under Article 21",
    "Procedure for filing a civil suit"
  ];

  const handleAsk = async () => {
    if (!query.trim()) {
      toast({
        title: "Input Required",
        description: "Please enter a legal question to get started.",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    setResponse("");
    setReferences([]);

    try {
      const res = await axios.post(
        `${BACKEND_URL}/ask`,
        { query },
        { 
          headers: { "Content-Type": "application/json" }, 
          timeout: 90000 
        }
      );
      
      setResponse(res.data?.answer || "No response received from the AI system.");
      setReferences(res.data?.references || []);
      
      toast({
        title: "Analysis Complete",
        description: "Your legal question has been successfully analyzed.",
      });
    } catch (error) {
      const errorMessage = error?.response?.data?.detail || error?.message || "An unexpected error occurred.";
      setResponse(`Error: ${errorMessage}`);
      
      toast({
        title: "Analysis Failed",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast({
        title: "File Required",
        description: "Please select a PDF, DOCX, or TXT file to upload.",
        variant: "destructive"
      });
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      toast({
        title: "File Too Large",
        description: "Please upload a file smaller than 15MB.",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    setUploadingPct(0);
    setResponse("");
    setReferences([]);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await axios.post(`${BACKEND_URL}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 120000,
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadingPct(percentCompleted);
          }
        },
      });

      setResponse(
        `📂 File: ${res.data?.filename || file.name}\n\n🧾 Analysis:\n${
          res.data?.analysis || "No analysis returned."
        }`
      );
      setReferences(res.data?.references || []);
      
      toast({
        title: "Upload Successful",
        description: "Your document has been analyzed successfully.",
      });
    } catch (error) {
      const errorMessage = error?.response?.data?.detail || error?.message || "Upload failed. Please try again.";
      setResponse(`Upload Error: ${errorMessage}`);
      
      toast({
        title: "Upload Failed",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
      setUploadingPct(null);
    }
  };

  const handleCopy = async () => {
    if (!response) return;

    try {
      await navigator.clipboard.writeText(response);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      
      toast({
        title: "Copied Successfully",
        description: "Response has been copied to your clipboard.",
      });
    } catch {
      toast({
        title: "Copy Failed",
        description: "Failed to copy to clipboard.",
        variant: "destructive"
      });
    }
  };

  const clearAll = () => {
    setQuery("");
    setResponse("");
    setReferences([]);
    setFile(null);
    setUploadingPct(null);
    setCopied(false);
  };

  return (
    <div className="min-h-screen bg-gradient-hero">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <motion.header
          initial={{ opacity: 0, y: -30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="flex items-center justify-center mb-6">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
              className="relative"
            >
              <ScaleIcon />
              <div className="absolute inset-0 animate-pulse-glow rounded-full" />
            </motion.div>
          </div>
          
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.6 }}
            className="font-display text-5xl lg:text-6xl font-bold mb-4 bg-gradient-to-r from-foreground via-accent to-primary-glow bg-clip-text text-transparent"
          >
            Legal AI Consultant
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.6 }}
            className="text-lg text-muted-foreground max-w-2xl mx-auto"
          >
            Advanced AI-powered legal consultation platform providing intelligent analysis and expert guidance for your legal questions.
          </motion.p>
        </motion.header>

        <motion.main
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="card-elegant"
        >
          <div className="mb-8">
            <h3 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wide">
              Quick Start - Sample Questions
            </h3>
            <div className="flex flex-wrap gap-2">
              {samples.map((sample, index) => (
                <motion.button
                  key={sample}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + index * 0.1, duration: 0.4 }}
                  onClick={() => setQuery(sample)}
                  className="chip-elegant"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {sample}
                </motion.button>
              ))}
            </div>
          </div>

          <div className="mb-6">
            <label htmlFor="query" className="block text-sm font-medium text-foreground mb-3">
              Your Legal Question
            </label>
            <Textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask your legal question here... For example: 'What are the legal requirements for filing a defamation case?'"
              className="input-elegant min-h-[120px] resize-none"
              disabled={loading}
            />
          </div>

          <div className="flex flex-wrap gap-3 mb-6">
            <Button
              onClick={handleAsk}
              disabled={loading || !query.trim()}
              className="btn-primary flex-1 min-w-[120px]"
            >
              {loading && !uploadingPct ? (
                <>
                  <LoadingIcon className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <ScaleIcon className="w-4 h-4 mr-2" />
                  Ask AI
                </>
              )}
            </Button>
            
            <Button
              onClick={clearAll}
              disabled={loading}
              variant="ghost"
              className="btn-ghost"
            >
              <ClearIcon className="w-4 h-4 mr-2" />
              Clear All
            </Button>
          </div>

          <div className="border-t border-border pt-6">
            <h3 className="text-sm font-semibold text-foreground mb-4">
              Document Analysis
            </h3>
            <div className="upload-zone">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <input
                    type="file"
                    accept=".pdf,.docx,.txt"
                    onChange={(e) => setFile(e.target.files?.[0] || null)}
                    className="w-full text-sm text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-accent file:text-accent-foreground file:font-medium hover:file:bg-accent/90 file:cursor-pointer"
                    disabled={loading}
                  />
                  {file && (
                    <p className="text-xs text-muted-foreground mt-2">
                      Selected: {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                    </p>
                  )}
                </div>
                
                <Button
                  onClick={handleUpload}
                  disabled={loading || !file}
                  className="btn-accent whitespace-nowrap"
                >
                  {uploadingPct !== null ? (
                    <>
                      <LoadingIcon className="w-4 h-4 mr-2 animate-spin" />
                      {uploadingPct}%
                    </>
                  ) : (
                    <>
                      <UploadIcon className="w-4 h-4 mr-2" />
                      Analyze Document
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </motion.main>

        <AnimatePresence>
          {response && (
            <motion.section
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -30 }}
              transition={{ duration: 0.5 }}
              className="answer-elegant"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <DocumentIcon className="w-6 h-6 text-accent" />
                  <h3 className="text-xl font-semibold">AI Analysis</h3>
                </div>
                
                <Button
                  onClick={handleCopy}
                  size="sm"
                  variant="ghost"
                  className={`transition-all duration-300 ${copied ? 'text-success' : ''}`}
                >
                  {copied ? (
                    <>
                      <CheckIcon className="w-4 h-4 mr-2" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <CopyIcon className="w-4 h-4 mr-2" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
              
              <div className="bg-background/50 rounded-lg p-6 border border-border">
                <pre className="whitespace-pre-wrap text-sm leading-relaxed text-foreground font-sans overflow-x-auto">
                  {response}
                </pre>
              </div>

              {references.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  transition={{ delay: 0.3, duration: 0.4 }}
                  className="mt-6 pt-6 border-t border-border"
                >
                  <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <DocumentIcon className="w-5 h-5 text-accent" />
                    Legal References
                  </h4>
                  <ul className="space-y-2">
                    {references.map((ref, index) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4 + index * 0.1, duration: 0.3 }}
                        className="flex items-start gap-3 p-3 rounded-lg bg-muted/20 border border-border/50"
                      >
                        <div className="w-2 h-2 rounded-full bg-accent mt-2 flex-shrink-0" />
                        <span className="text-sm italic text-muted-foreground">
                          {ref.source}
                        </span>
                      </motion.li>
                    ))}
                  </ul>
                </motion.div>
              )}
            </motion.section>
          )}
        </AnimatePresence>

        <motion.footer
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1, duration: 0.6 }}
          className="text-center mt-12 text-sm text-muted-foreground"
        >
          <p>Backend: {BACKEND_URL}</p>
          <p className="mt-2 text-xs">
            ⚖️ Professional Legal AI Consultation Platform - Built with Advanced AI Technology
          </p>
        </motion.footer>
      </div>
    </div>
  );
}