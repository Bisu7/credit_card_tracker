import React, { useState, useEffect, useRef } from 'react';
import { 
  BookOpen, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  Copy, 
  Download,
  Share2,
  Star,
  Clock,
  Brain,
  AlertCircle,
  FileText,
  FileCode,
  File
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import toast from 'react-hot-toast';

interface ResultsDisplayProps {
  results: any;
}

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results }) => {
  const [expandedSources, setExpandedSources] = useState<Set<number>>(new Set());
  const [showReasoning, setShowReasoning] = useState(false);
  const [showExportMenu, setShowExportMenu] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  // Close export menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (exportMenuRef.current && !exportMenuRef.current.contains(event.target as Node)) {
        setShowExportMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleSource = (index: number) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSources(newExpanded);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const exportResearch = (format: 'txt' | 'md' | 'json') => {
    if (!results || !results.success) return;

    const { research_report, execution_time, sources_found, reasoning_steps } = results;
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `deep-research-${timestamp}`;

    let content = '';
    let mimeType = '';
    let fileExtension = '';

    switch (format) {
      case 'txt':
        content = generateTextExport(research_report, execution_time, sources_found, reasoning_steps);
        mimeType = 'text/plain';
        fileExtension = 'txt';
        break;
      case 'md':
        content = generateMarkdownExport(research_report, execution_time, sources_found, reasoning_steps);
        mimeType = 'text/markdown';
        fileExtension = 'md';
        break;
      case 'json':
        content = JSON.stringify(results, null, 2);
        mimeType = 'application/json';
        fileExtension = 'json';
        break;
    }

    downloadFile(content, `${filename}.${fileExtension}`, mimeType);
    toast.success(`Research exported as ${format.toUpperCase()}`);
  };

  const generateTextExport = (research_report: any, execution_time: number, sources_found: number, reasoning_steps: number) => {
    const timestamp = new Date().toLocaleString();
    
    let content = `DEEP RESEARCHER - RESEARCH REPORT\n`;
    content += `Generated on: ${timestamp}\n`;
    content += `Execution Time: ${formatTime(execution_time)}\n`;
    content += `Sources Found: ${sources_found}\n`;
    content += `Reasoning Steps: ${reasoning_steps}\n`;
    content += `Confidence Score: ${Math.round(research_report.confidence_score * 100)}%\n`;
    content += `\n${'='.repeat(50)}\n\n`;
    
    // Research Summary
    content += `RESEARCH SUMMARY\n`;
    content += `${'='.repeat(20)}\n\n`;
    content += research_report.summary.replace(/<[^>]*>/g, '').replace(/\n\s*\n/g, '\n\n');
    
    // Key Findings
    if (research_report.key_findings && research_report.key_findings.length > 0) {
      content += `\n\nKEY FINDINGS\n`;
      content += `${'='.repeat(15)}\n\n`;
      research_report.key_findings.forEach((finding: string, index: number) => {
        content += `${index + 1}. ${finding}\n`;
      });
    }
    
    // Sources
    if (research_report.sources && research_report.sources.length > 0) {
      content += `\n\nSOURCES\n`;
      content += `${'='.repeat(10)}\n\n`;
      research_report.sources.forEach((source: any, index: number) => {
        content += `Source ${index + 1}:\n`;
        content += `Title: ${source.title || 'Untitled'}\n`;
        if (source.relevance_score) {
          content += `Relevance: ${Math.round(source.relevance_score * 100)}%\n`;
        }
        content += `Content: ${source.content.replace(/<[^>]*>/g, '').substring(0, 500)}...\n\n`;
      });
    }
    
    return content;
  };

  const generateMarkdownExport = (research_report: any, execution_time: number, sources_found: number, reasoning_steps: number) => {
    const timestamp = new Date().toLocaleString();
    
    let content = `# Deep Researcher - Research Report\n\n`;
    content += `**Generated on:** ${timestamp}\n`;
    content += `**Execution Time:** ${formatTime(execution_time)}\n`;
    content += `**Sources Found:** ${sources_found}\n`;
    content += `**Reasoning Steps:** ${reasoning_steps}\n`;
    content += `**Confidence Score:** ${Math.round(research_report.confidence_score * 100)}%\n\n`;
    content += `---\n\n`;
    
    // Research Summary
    content += `## Research Summary\n\n`;
    content += research_report.summary;
    
    // Key Findings
    if (research_report.key_findings && research_report.key_findings.length > 0) {
      content += `\n\n## Key Findings\n\n`;
      research_report.key_findings.forEach((finding: string, index: number) => {
        content += `${index + 1}. ${finding}\n`;
      });
    }
    
    // Sources
    if (research_report.sources && research_report.sources.length > 0) {
      content += `\n\n## Sources\n\n`;
      research_report.sources.forEach((source: any, index: number) => {
        content += `### Source ${index + 1}\n\n`;
        content += `**Title:** ${source.title || 'Untitled'}\n\n`;
        if (source.relevance_score) {
          content += `**Relevance:** ${Math.round(source.relevance_score * 100)}%\n\n`;
        }
        content += `**Content:**\n\n${source.content}\n\n`;
        content += `---\n\n`;
      });
    }
    
    return content;
  };

  const downloadFile = (content: string, filename: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const formatConfidence = (score: number) => {
    const percentage = Math.round(score * 100);
    const color = percentage >= 80 ? 'text-green-600' : percentage >= 60 ? 'text-yellow-600' : 'text-red-600';
    return (
      <span className={`font-medium ${color}`}>
        {percentage}% confidence
      </span>
    );
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    }
    return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  };

  if (!results || !results.success) {
    return (
      <div className="mt-8 p-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
        <div className="flex items-center space-x-2 mb-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <h3 className="text-lg font-semibold text-red-800 dark:text-red-200">
            Research Failed
          </h3>
        </div>
        <p className="text-red-600 dark:text-red-300 mb-3">
          {results?.error || 'An error occurred while processing your query.'}
        </p>
        <div className="text-sm text-red-500 dark:text-red-400">
          <p>• Check if the backend server is running</p>
          <p>• Verify your internet connection</p>
          <p>• Try a simpler query</p>
        </div>
      </div>
    );
  }

  const { research_report, execution_time, sources_found, reasoning_steps } = results;

  return (
    <div className="mt-8 space-y-8">
      {/* Research Summary - Enhanced */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* Header with enhanced styling */}
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-700 dark:to-gray-600 px-6 py-4 border-b border-gray-200 dark:border-gray-600">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                <Brain className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                  Research Summary
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Comprehensive analysis and insights
                </p>
              </div>
            </div>
            
            {/* Enhanced metrics */}
            <div className="flex flex-wrap items-center gap-4 text-sm">
              <div className="flex items-center space-x-2 px-3 py-1 bg-white dark:bg-gray-800 rounded-full border border-gray-200 dark:border-gray-600">
                <Clock className="w-4 h-4 text-gray-500" />
                <span className="font-medium text-gray-700 dark:text-gray-300">{formatTime(execution_time)}</span>
              </div>
              <div className="flex items-center space-x-2 px-3 py-1 bg-white dark:bg-gray-800 rounded-full border border-gray-200 dark:border-gray-600">
                <BookOpen className="w-4 h-4 text-gray-500" />
                <span className="font-medium text-gray-700 dark:text-gray-300">{sources_found} sources</span>
              </div>
              <div className="flex items-center space-x-2 px-3 py-1 bg-white dark:bg-gray-800 rounded-full border border-gray-200 dark:border-gray-600">
                <Star className="w-4 h-4 text-yellow-500" />
                {formatConfidence(research_report.confidence_score)}
              </div>
            </div>
          </div>
        </div>

        {/* Content with enhanced styling */}
        <div className="p-6">
          <div className="prose prose-lg prose-gray dark:prose-invert max-w-none">
            <ReactMarkdown
              components={{
                h1: ({ children }) => (
                  <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-6 border-b border-gray-200 dark:border-gray-700 pb-3">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4 mt-8">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-3 mt-6">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="text-gray-700 dark:text-gray-300 mb-4 leading-relaxed">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="space-y-2 mb-4">
                    {children}
                  </ul>
                ),
                li: ({ children }) => (
                  <li className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">{children}</span>
                  </li>
                ),
                code({ node, inline, className, children, ...props }: any) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline && match ? (
                    <SyntaxHighlighter
                      style={tomorrow as any}
                      language={match[1]}
                      PreTag="div"
                      className="rounded-lg my-4"
                      {...props}
                    >
                      {String(children).replace(/\n$/, '')}
                    </SyntaxHighlighter>
                  ) : (
                    <code className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-sm font-mono text-gray-800 dark:text-gray-200" {...props}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {research_report.summary}
            </ReactMarkdown>
          </div>

          {/* Enhanced action buttons */}
          <div className="flex flex-wrap items-center gap-3 mt-6 pt-6 border-t border-gray-200 dark:border-gray-700 relative">
            <button
              onClick={() => copyToClipboard(research_report.summary)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
            >
              <Copy className="w-4 h-4" />
              <span className="font-medium">Copy Summary</span>
            </button>
            
            {/* Export Dropdown */}
            <div className="relative inline-block" ref={exportMenuRef}>
              <button
                onClick={() => setShowExportMenu(!showExportMenu)}
                className="flex items-center space-x-2 px-4 py-2 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/50 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span className="font-medium">Export</span>
                <ChevronDown className="w-4 h-4" />
              </button>
              
              {showExportMenu && (
                <div className="absolute top-full left-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-2xl border border-gray-200 dark:border-gray-700 z-[9999] overflow-hidden transform translate-y-0">
                  <div className="py-2">
                    <button
                      onClick={() => {
                        exportResearch('txt');
                        setShowExportMenu(false);
                      }}
                      className="w-full flex items-center space-x-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <FileText className="w-4 h-4 text-gray-500 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-gray-300 font-medium">Export as TXT</span>
                    </button>
                    <button
                      onClick={() => {
                        exportResearch('md');
                        setShowExportMenu(false);
                      }}
                      className="w-full flex items-center space-x-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <FileCode className="w-4 h-4 text-gray-500 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-gray-300 font-medium">Export as Markdown</span>
                    </button>
                    <button
                      onClick={() => {
                        exportResearch('json');
                        setShowExportMenu(false);
                      }}
                      className="w-full flex items-center space-x-3 px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <File className="w-4 h-4 text-gray-500 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-gray-300 font-medium">Export as JSON</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
            
            <button className="flex items-center space-x-2 px-4 py-2 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-lg hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors">
              <Share2 className="w-4 h-4" />
              <span className="font-medium">Share</span>
            </button>
          </div>
        </div>
      </div>

      {/* Key Findings - Enhanced */}
      {research_report.key_findings && research_report.key_findings.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-gray-700 dark:to-gray-600 px-6 py-4 border-b border-gray-200 dark:border-gray-600">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
                <Star className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  Key Findings
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {research_report.key_findings.length} important insights discovered
                </p>
              </div>
            </div>
          </div>
          
          <div className="p-6">
            <div className="grid gap-4">
              {research_report.key_findings.map((finding: string, index: number) => (
                <div key={index} className="flex items-start space-x-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                  <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center">
                    <span className="text-sm font-bold text-green-600 dark:text-green-400">
                      {index + 1}
                    </span>
                  </div>
                  <div className="flex-1">
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                      {finding}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Reasoning Process - Enhanced */}
      {reasoning_steps > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <button
            onClick={() => setShowReasoning(!showReasoning)}
            className="w-full text-left"
          >
            <div className="bg-gradient-to-r from-purple-50 to-violet-50 dark:from-gray-700 dark:to-gray-600 px-6 py-4 border-b border-gray-200 dark:border-gray-600">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                    <Brain className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                      AI Reasoning Process
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {reasoning_steps} analytical steps completed
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="px-3 py-1 bg-purple-100 dark:bg-purple-900 rounded-full">
                    <span className="text-sm font-medium text-purple-700 dark:text-purple-300">
                      {reasoning_steps} steps
                    </span>
                  </div>
                  {showReasoning ? (
                    <ChevronUp className="w-6 h-6 text-gray-500" />
                  ) : (
                    <ChevronDown className="w-6 h-6 text-gray-500" />
                  )}
                </div>
              </div>
            </div>
          </button>
          
          {showReasoning && (
            <div className="p-6">
              <div className="bg-gradient-to-r from-purple-50 to-violet-50 dark:from-purple-900/20 dark:to-violet-900/20 rounded-lg p-6 border border-purple-200 dark:border-purple-700">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-10 h-10 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center">
                    <Brain className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      Multi-Step Analysis
                    </h4>
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4">
                      The AI analyzed your query through {reasoning_steps} comprehensive reasoning steps to provide this detailed answer. 
                      This systematic approach ensures thorough analysis, cross-referencing of information, and accurate results.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full text-sm font-medium">
                        Query Analysis
                      </span>
                      <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full text-sm font-medium">
                        Information Gathering
                      </span>
                      <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full text-sm font-medium">
                        Synthesis
                      </span>
                      <span className="px-3 py-1 bg-purple-100 dark:bg-purple-900 text-purple-700 dark:text-purple-300 rounded-full text-sm font-medium">
                        Validation
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sources - Enhanced */}
      {research_report.sources && research_report.sources.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="bg-gradient-to-r from-orange-50 to-amber-50 dark:from-gray-700 dark:to-gray-600 px-6 py-4 border-b border-gray-200 dark:border-gray-600">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
                <BookOpen className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  Research Sources
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {research_report.sources.length} sources analyzed and referenced
                </p>
              </div>
            </div>
          </div>
          
          <div className="p-6">
            <div className="space-y-4">
              {research_report.sources.map((source: any, index: number) => (
                <div key={index} className="border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
                  <button
                    onClick={() => toggleSource(index)}
                    className="w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex-shrink-0 w-10 h-10 bg-orange-100 dark:bg-orange-900 rounded-full flex items-center justify-center">
                          <span className="text-sm font-bold text-orange-600 dark:text-orange-400">
                            {index + 1}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-900 dark:text-white truncate">
                            {source.title || `Source ${index + 1}`}
                          </h4>
                          {source.relevance_score && (
                            <div className="flex items-center space-x-2 mt-1">
                              <div className="flex items-center space-x-1">
                                <Star className="w-3 h-3 text-yellow-500" />
                                <span className="text-sm text-gray-600 dark:text-gray-400">
                                  {Math.round(source.relevance_score * 100)}% relevant
                                </span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {source.relevance_score && (
                          <div className="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                            <div 
                              className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                              style={{ width: `${source.relevance_score * 100}%` }}
                            />
                          </div>
                        )}
                        {expandedSources.has(index) ? (
                          <ChevronUp className="w-5 h-5 text-gray-500" />
                        ) : (
                          <ChevronDown className="w-5 h-5 text-gray-500" />
                        )}
                      </div>
                    </div>
                  </button>
                  
                  {expandedSources.has(index) && (
                    <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700/30">
                      <div className="mt-4 prose prose-sm prose-gray dark:prose-invert max-w-none">
                        <ReactMarkdown
                          components={{
                            p: ({ children }) => (
                              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-3">
                                {children}
                              </p>
                            ),
                          }}
                        >
                          {source.content}
                        </ReactMarkdown>
                      </div>
                      <div className="mt-4 flex items-center space-x-3">
                        <button
                          onClick={() => copyToClipboard(source.content)}
                          className="flex items-center space-x-2 px-3 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
                        >
                          <Copy className="w-3 h-3" />
                          <span className="text-sm font-medium">Copy</span>
                        </button>
                        <button className="flex items-center space-x-2 px-3 py-1 bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-lg hover:bg-green-100 dark:hover:bg-green-900/50 transition-colors">
                          <ExternalLink className="w-3 h-3" />
                          <span className="text-sm font-medium">View Source</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsDisplay;
