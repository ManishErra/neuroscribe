import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useAsk } from '@/features/search/hooks/useAsk';
import { usePatient } from '@/features/patients/hooks/usePatient';
import { isStructuredAnswer, isStructuredAnswerArray } from '@/features/search/types/search.types';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { useSettings } from '@/store/SettingsContext';
import { cn } from '@/lib/utils';
import { 
  Sparkles, 
  Search, 
  FileText, 
  AlertTriangle, 
  Brain, 
  ArrowRight,
  ChevronDown
} from 'lucide-react';

export default function AskTab() {
  const { patientId } = useParams<{ patientId: string }>();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';
  
  const { data: patient } = usePatient(patientId);
  const askMutation = useAsk();

  const [query, setQuery] = useState('');
  const [showSources, setShowSources] = useState(false);

  const handleAsk = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || askMutation.isPending) return;
    
    // Auto-inject context to ground the search slightly more to this patient 
    // even if the vector DB currently searches all doctor's documents.
    const contextualQuery = `Regarding patient ${patient?.name || 'this patient'}: ${query}`;
    askMutation.mutate(contextualQuery);
  };

  const renderAnswer = () => {
    if (!askMutation.data) return null;
    const { answer } = askMutation.data;

    if (isStructuredAnswerArray(answer)) {
      return (
        <div className="flex flex-col gap-4 w-full">
          {answer.map((ans, idx) => (
            <div key={idx} className="bg-white border border-border p-4 rounded-lg shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-bold text-[#003d9b] capitalize">{ans.test}</span>
                {ans.confidence_label && (
                  <Badge variant="outline" className={cn(
                    "text-[10px] font-bold px-2 py-0.5",
                    ans.confidence_label === 'HIGH' ? "border-emerald-200 bg-emerald-50 text-emerald-700" :
                    ans.confidence_label === 'MEDIUM' ? "border-amber-200 bg-amber-50 text-amber-700" :
                    "border-rose-200 bg-rose-50 text-rose-700"
                  )}>
                    {ans.confidence_label} Confidence
                  </Badge>
                )}
              </div>
              <div className="flex items-end gap-2 mb-3">
                <span className="text-2xl font-bold text-[#191c1d]">{ans.value}</span>
                {ans.unit && <span className="text-sm font-semibold text-[#747783] mb-1">{ans.unit}</span>}
              </div>
              {ans.status && (
                <span className={cn(
                  "text-xs font-semibold px-2 py-1 rounded-md",
                  ans.status.toUpperCase().includes('NORMAL') ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
                )}>
                  {ans.status}
                </span>
              )}
            </div>
          ))}
        </div>
      );
    }

    if (isStructuredAnswer(answer)) {
      return (
        <div className="bg-white border border-border p-4 rounded-lg shadow-sm w-full">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-bold text-[#003d9b] capitalize">{answer.test}</span>
            {answer.confidence_label && (
              <Badge variant="outline" className="text-[10px] font-bold px-2 py-0.5 border-emerald-200 bg-emerald-50 text-emerald-700">
                {answer.confidence_label} Confidence
              </Badge>
            )}
          </div>
          <div className="flex items-end gap-2">
            <span className="text-2xl font-bold text-[#191c1d]">{answer.value}</span>
            {answer.unit && <span className="text-sm font-semibold text-[#747783] mb-1">{answer.unit}</span>}
          </div>
        </div>
      );
    }

    // Default string fallback
    return (
      <div className="bg-white border border-border p-5 rounded-lg shadow-sm w-full">
        <p className="text-sm leading-relaxed text-[#191c1d] whitespace-pre-wrap font-medium">
          {typeof answer === 'string' ? answer : JSON.stringify(answer, null, 2)}
        </p>
      </div>
    );
  };

  return (
    <div className={cn('flex flex-col max-w-4xl mx-auto w-full select-none animate-in fade-in duration-300', isCompact ? 'gap-4 pt-4' : 'gap-6 pt-6')}>
      
      {/* ── Search Input Area ───────────────────────────────────── */}
      <Card className="bg-white border-border shadow-sm rounded-xl overflow-hidden relative">
        <div className="absolute top-0 right-0 w-32 h-32 bg-[#003d9b]/5 rounded-full blur-3xl pointer-events-none" />
        <CardHeader className={cn('border-b border-border bg-[#f8f9fa]', isCompact ? 'py-3 px-4' : 'py-5 px-6')}>
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-[#003d9b]/10 border border-[#003d9b]/20 flex items-center justify-center text-[#003d9b] shrink-0">
              <Brain className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-sm font-bold tracking-wide text-[#191c1d] uppercase">
                Ask NeuroScribe
              </CardTitle>
              <p className="text-xs text-[#747783] mt-0.5">
                Query the clinical memory bank for {patient?.name}.
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent className={cn('bg-white', isCompact ? 'p-4' : 'p-6')}>
          <form onSubmit={handleAsk} className="flex flex-col gap-3">
            <div className="relative flex items-center w-full">
              <Search className="absolute left-4 h-5 w-5 text-[#747783]" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., What was the latest hemoglobin reading?"
                disabled={askMutation.isPending}
                className={cn(
                  "w-full bg-[#f8f9fa] border border-border rounded-xl text-sm font-medium text-[#191c1d] placeholder:text-[#747783] focus:outline-none focus:ring-2 focus:ring-[#003d9b]/20 focus:border-[#003d9b] transition-all pl-12 pr-4 disabled:opacity-50 select-text",
                  isCompact ? "h-12" : "h-14"
                )}
              />
              <button
                type="submit"
                disabled={!query.trim() || askMutation.isPending}
                className={cn(
                  "absolute right-2 inline-flex items-center justify-center rounded-lg bg-[#003d9b] hover:bg-[#00296d] text-white shadow-sm transition-all disabled:opacity-50 active:scale-95",
                  isCompact ? "h-8 px-3" : "h-10 px-4"
                )}
              >
                {askMutation.isPending ? (
                  <Sparkles className="h-4 w-4 animate-pulse fill-current" />
                ) : (
                  <>
                    <span className="text-xs font-bold mr-1">Ask</span>
                    <ArrowRight className="h-3.5 w-3.5" />
                  </>
                )}
              </button>
            </div>
            <div className="flex gap-2 flex-wrap">
              <span className="text-[10px] font-bold text-[#747783] uppercase tracking-wider py-1">Suggestions:</span>
              <button type="button" onClick={() => setQuery("What are the active medications?")} className="text-[10px] font-semibold text-[#003d9b] bg-[#003d9b]/5 hover:bg-[#003d9b]/10 border border-[#003d9b]/20 rounded-full px-2.5 py-1 transition-colors">Active Medications</button>
              <button type="button" onClick={() => setQuery("Summarize the last consultation.")} className="text-[10px] font-semibold text-[#003d9b] bg-[#003d9b]/5 hover:bg-[#003d9b]/10 border border-[#003d9b]/20 rounded-full px-2.5 py-1 transition-colors">Last Consultation</button>
              <button type="button" onClick={() => setQuery("Any recent abnormal lab results?")} className="text-[10px] font-semibold text-[#003d9b] bg-[#003d9b]/5 hover:bg-[#003d9b]/10 border border-[#003d9b]/20 rounded-full px-2.5 py-1 transition-colors">Abnormal Labs</button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* ── Results Area ────────────────────────────────────────── */}
      {askMutation.isPending && (
        <Card className="bg-white border-border shadow-sm rounded-xl overflow-hidden animate-pulse">
          <CardContent className={isCompact ? 'p-4' : 'p-6'}>
            <div className="flex items-center gap-3 mb-4">
              <Skeleton className="h-8 w-8 rounded-full" />
              <div className="space-y-2 flex-1">
                <Skeleton className="h-4 w-1/4" />
                <Skeleton className="h-3 w-1/3" />
              </div>
            </div>
            <div className="space-y-3">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/5" />
            </div>
          </CardContent>
        </Card>
      )}

      {askMutation.isError && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-6 text-center shadow-sm">
          <AlertTriangle className="h-8 w-8 text-rose-500 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-rose-700 mb-1">Search Failed</h3>
          <p className="text-xs text-rose-600/80 max-w-sm mx-auto">
            {askMutation.error instanceof Error ? askMutation.error.message : 'An error occurred while communicating with the intelligence engine.'}
          </p>
        </div>
      )}

      {askMutation.isSuccess && askMutation.data && (
        <div className="flex flex-col gap-4 animate-in fade-in duration-300">
          
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-full bg-[#003d9b] shadow-md border-4 border-white flex items-center justify-center shrink-0 z-10">
              <Sparkles className="h-4 w-4 text-white fill-current" />
            </div>
            <div className="flex-1 flex flex-col gap-2 pt-1 min-w-0">
              {renderAnswer()}
            </div>
          </div>

          {/* Citations / Source Chunks */}
          {askMutation.data.chunks_used && askMutation.data.chunks_used.length > 0 && (
            <div className="ml-14 flex flex-col gap-2">
              <button 
                onClick={() => setShowSources(!showSources)}
                className="flex items-center gap-1.5 text-xs font-bold text-[#747783] hover:text-[#191c1d] transition-colors w-fit"
              >
                <ChevronDown className={cn("h-4 w-4 transition-transform", showSources && "rotate-180")} />
                {showSources ? "Hide Sources" : `View ${askMutation.data.chunks_used.length} Clinical Sources`}
              </button>
              
              {showSources && (
                <div className="flex flex-col gap-3 mt-2 animate-in slide-in-from-top-2 duration-200">
                  {askMutation.data.chunks_used.map((chunk, idx) => (
                    <Card key={idx} className="bg-[#f8f9fa] border-border shadow-none rounded-lg overflow-hidden">
                      <CardHeader className="p-3 border-b border-border bg-white flex flex-row items-center justify-between">
                        <div className="flex items-center gap-2">
                          <FileText className="h-3.5 w-3.5 text-[#003d9b]" />
                          <span className="text-[10px] font-bold text-[#191c1d] uppercase tracking-wider">Source Document</span>
                        </div>
                        <Badge variant="outline" className="text-[9px] font-bold border-border text-[#747783] px-1.5 py-0">
                          Score: {(chunk.similarity_score * 100).toFixed(1)}%
                        </Badge>
                      </CardHeader>
                      <CardContent className="p-3">
                        <p className="text-xs text-[#434652] leading-relaxed font-mono select-text">
                          "{chunk.chunk_text}"
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      )}

    </div>
  );
}
