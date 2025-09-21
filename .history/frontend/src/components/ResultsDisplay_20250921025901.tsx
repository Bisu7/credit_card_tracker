import React, { useState } from 'react';
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
  Brain
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
        <h3 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">
          Research Failed
        </h3>
        <p className="text-red-600 dark:text-red-300">
          {results?.error || 'An error occurred while processing your query.'}
        </p>
      </div>
    );
  }

  const { research_report, execution_time, sources_found, reasoning_steps } = results;

  return (
    <div className="mt-8 space-y-6">
      {/* Research Summary */}
      <div className="card p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Brain className="w-5 h-5 text-primary-500" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Research Summary
            </h2>
          </div>
          <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center space-x-1">
              <Clock className="w-4 h-4" />
              <span>{formatTime(execution_time)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <BookOpen className="w-4 h-4" />
              <span>{sources_found} sources</span>
            </div>
            <div className="flex items-center space-x-1">
              <Star className="w-4 h-4" />
              {formatConfidence(research_report.confidence_score)}
            </div>
          </div>
        </div>

        <div className="prose prose-gray dark:prose-invert max-w-none">
          <ReactMarkdown
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <SyntaxHighlighter
                    style={tomorrow}
                    language={match[1]}
                    PreTag="div"
                    {...props}
                  >
                    {String(children).replace(/\n$/, '')}
                  </SyntaxHighlighter>
                ) : (
                  <code className={className} {...props}>
                    {children}
                  </code>
                );
              },
            }}
          >
            {research_report.summary}
          </ReactMarkdown>
        </div>

        {/* Action buttons */}
        <div className="flex items-center space-x-2 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => copyToClipboard(research_report.summary)}
            className="flex items-center space-x-1 px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <Copy className="w-4 h-4" />
            <span>Copy</span>
          </button>
          <button className="flex items-center space-x-1 px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
          <button className="flex items-center space-x-1 px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
            <Share2 className="w-4 h-4" />
            <span>Share</span>
          </button>
        </div>
      </div>

      {/* Key Findings */}
      {research_report.key_findings && research_report.key_findings.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Key Findings
          </h3>
          <ul className="space-y-2">
            {research_report.key_findings.map((finding: string, index: number) => (
              <li key={index} className="flex items-start space-x-2">
                <div className="w-2 h-2 bg-primary-500 rounded-full mt-2 flex-shrink-0" />
                <span className="text-gray-700 dark:text-gray-300">{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Reasoning Process */}
      {reasoning_steps > 0 && (
        <div className="card p-6">
          <button
            onClick={() => setShowReasoning(!showReasoning)}
            className="flex items-center justify-between w-full text-left"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Reasoning Process ({reasoning_steps} steps)
            </h3>
            {showReasoning ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </button>
          {showReasoning && (
            <div className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                The AI analyzed your query through {reasoning_steps} reasoning steps to provide this comprehensive answer.
                This multi-step approach ensures thorough analysis and accurate results.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Sources */}
      {research_report.sources && research_report.sources.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Sources ({research_report.sources.length})
          </h3>
          <div className="space-y-3">
            {research_report.sources.map((source: any, index: number) => (
              <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg">
                <button
                  onClick={() => toggleSource(index)}
                  className="w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <BookOpen className="w-4 h-4 text-primary-500 flex-shrink-0" />
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white">
                          {source.title || `Source ${index + 1}`}
                        </h4>
                        {source.relevance_score && (
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            Relevance: {Math.round(source.relevance_score * 100)}%
                          </p>
                        )}
                      </div>
                    </div>
                    {expandedSources.has(index) ? (
                      <ChevronUp className="w-5 h-5 text-gray-500" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-gray-500" />
                    )}
                  </div>
                </button>
                
                {expandedSources.has(index) && (
                  <div className="px-4 pb-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="mt-4 prose prose-sm prose-gray dark:prose-invert max-w-none">
                      <ReactMarkdown>{source.content}</ReactMarkdown>
                    </div>
                    <div className="mt-3 flex items-center space-x-2">
                      <button
                        onClick={() => copyToClipboard(source.content)}
                        className="flex items-center space-x-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                      >
                        <Copy className="w-3 h-3" />
                        <span>Copy</span>
                      </button>
                      <button className="flex items-center space-x-1 text-xs text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                        <ExternalLink className="w-3 h-3" />
                        <span>View</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ResultsDisplay;
