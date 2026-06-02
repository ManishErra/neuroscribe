/* eslint-disable @typescript-eslint/no-explicit-any, react-hooks/set-state-in-effect, react-hooks/purity */
// SessionDetailPage — unified clinical consultations workspace.
// Architecture ref: frontend_architecture.md §4, §5.4, §8, §16.1

import { useParams, Link } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import { useSession } from '@/features/sessions/hooks/useSession';
import { usePatient } from '@/features/patients/hooks/usePatient';
import { useUploadAudio } from '@/features/sessions/hooks/useUploadAudio';
import { useGenerateNote } from '@/features/notes/hooks/useGenerateNote';
import { useSaveNote } from '@/features/notes/hooks/useSaveNote';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Mic, Square, Volume2, Sparkles, CheckCircle2, Lock, AlertTriangle, Copy, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ClinicalNote } from '@/features/sessions/services/sessions.service';

export default function SessionDetailPage() {
  const { patientId, sessionId } = useParams<{ patientId: string; sessionId: string }>();

  // Queries
  const { data: patient, isLoading: isPatientLoading } = usePatient(patientId);
  const { data: session, isLoading: isSessionLoading, isError: isSessionError } = useSession(sessionId);

  // Mutations
  const uploadAudioMutation = useUploadAudio(patientId);
  const generateNoteMutation = useGenerateNote();
  const saveNoteMutation = useSaveNote();

  // Local state for browser audio recording
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<any>(null);

  // Local state for SOAP Note Editor form
  const [soapTab, setSoapTab] = useState<'subjective' | 'objective' | 'assessment' | 'plan'>('subjective');
  const [noteId, setNoteId] = useState<string>('');
  const [symptomsText, setSymptomsText] = useState('');
  const [medicationsText, setMedicationsText] = useState('');
  const [isNoteFinalized, setIsNoteFinalized] = useState(false);
  const [noteState, setNoteState] = useState<ClinicalNote>({
    presenting_complaint: '',
    symptoms_mentioned: [],
    medications_mentioned: [],
    sleep: '',
    mood_in_patient_words: '',
    social_context: '',
    plan_discussed: '',
    flags_for_review: '',
    confidence: '',
  });

  // Sync session details on load
  useEffect(() => {
    if (session) {
      setIsNoteFinalized(session.note_finalized);
      if (session.note) {
        setNoteState(session.note);
        setSymptomsText(session.note.symptoms_mentioned?.join(', ') || '');
        setMedicationsText(session.note.medications_mentioned?.join(', ') || '');
      }
    }
  }, [session]);

  // Sync generated note ID from generate note mutation
  useEffect(() => {
    if (generateNoteMutation.data) {
      const generated = generateNoteMutation.data;
      setNoteId(generated.note_id);
      setNoteState(generated.ai_draft);
      setSymptomsText(generated.ai_draft.symptoms_mentioned?.join(', ') || '');
      setMedicationsText(generated.ai_draft.medications_mentioned?.join(', ') || '');
    }
  }, [generateNoteMutation.data]);

  // Duration timer ticker helper
  useEffect(() => {
    if (isRecording) {
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording]);

  // format recording seconds to MM:SS
  const formatRecordingTime = (totalSecs: number) => {
    const mins = Math.floor(totalSecs / 60);
    const secs = totalSecs % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Browser Audio Capturing triggers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = mediaRecorder;
      
      const audioChunks: Blob[] = [];
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        setRecordedBlob(audioBlob);
        
        // Stop all audio stream tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      setRecordedBlob(null);
      setRecordingSeconds(0);
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error('[ERROR] Microphone access failed: ', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Upload captured audio blob and transcribe
  const handleUploadAudio = () => {
    if (!recordedBlob || !sessionId) return;
    
    const audioFile = new File([recordedBlob], 'consultation_session.webm', {
      type: 'audio/webm',
    });

    uploadAudioMutation.mutate({
      sessionId,
      audioFile,
    });
  };

  // Trigger AI SOAP note compilation from raw transcript
  const handleGenerateNote = () => {
    if (!session?.transcript || !patient || !sessionId) return;
    
    generateNoteMutation.mutate({
      transcriptId: sessionId, // In backend, transcript_id resolves to transcript key, let's keep it robust
      patientName: patient.name,
      patientAge: patient.age,
    });
  };

  // Submit finalised SOAP inputs
  const handleSaveNote = () => {
    if (!patientId || !sessionId) return;
    
    const targetNoteId = noteId || sessionId; // Resolves to either noteId from creation or sessionId as key

    // Convert comma textareas back to arrays
    const finalNote: ClinicalNote = {
      ...noteState,
      symptoms_mentioned: symptomsText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      medications_mentioned: medicationsText
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
    };

    saveNoteMutation.mutate({
      noteId: targetNoteId,
      doctorEdited: finalNote,
      sessionId,
      patientId,
    }, {
      onSuccess: () => {
        setIsNoteFinalized(true);
      },
    });
  };

  // Copy raw transcript contents helper
  const handleCopyTranscript = () => {
    if (session?.transcript) {
      navigator.clipboard.writeText(session.transcript);
    }
  };

  const isLoading = isPatientLoading || isSessionLoading;

  if (isSessionError) {
    return (
      <div className="p-6 text-center max-w-lg mx-auto mt-20">
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-rose-400 mb-2">Session Not Found</h3>
          <p className="text-xs text-muted-foreground mb-4">
            The consultation log could not be loaded from database.
          </p>
          <Link
            to={`/patients/${patientId}/sessions`}
            className="inline-flex items-center gap-2 text-xs font-semibold text-primary hover:underline"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Return to Patient Sessions
          </Link>
        </div>
      </div>
    );
  }

  // Visual text extractor helper for mock activity summaries
  const renderSummaryCard = () => {
    // If note exists (either final note, generated draft, or state draft)
    const hasNote = session?.note || generateNoteMutation.data;
    
    if (!hasNote) {
      return (
        <Card className="border border-white/[0.06] bg-slate-900/40 p-5 rounded-2xl select-none">
          <CardContent className="p-0 text-center py-4 text-xs font-semibold text-muted-foreground italic select-none">
            No summary generated yet.
          </CardContent>
        </Card>
      );
    }

    const summaryText = noteState.presenting_complaint || 'No complaint notes available.';
    const planText = noteState.plan_discussed || 'No clinical plans specified.';

    return (
      <Card className="border border-white/[0.06] bg-slate-900/40 p-5 rounded-2xl select-none relative overflow-hidden">
        <div className="absolute top-0 right-0 w-24 h-24 bg-[#508a7b]/5 rounded-full blur-2xl pointer-events-none" />
        <CardHeader className="p-0 mb-3 pb-3 border-b border-white/[0.04] flex flex-row items-center gap-2 select-none">
          <div className="h-6 w-6 rounded-lg bg-[#508a7b]/10 border border-[#508a7b]/20 flex items-center justify-center text-[#508a7b] shrink-0">
            <FileText className="h-3.5 w-3.5" />
          </div>
          <CardTitle className="text-xs font-bold uppercase tracking-widest text-[#508a7b]">
            Clinical Session Summary
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0 flex flex-col gap-3 text-xs leading-relaxed text-foreground/90 font-medium">
          <p>
            <strong>Presenting Complaint:</strong> {summaryText}
          </p>
          <p>
            <strong>Plan Discussed:</strong> {planText}
          </p>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1600px] mx-auto w-full select-none animate-in fade-in duration-300">
      
      {/* ── Breadcrumb & Header ─────────────────────────────────── */}
      <div className="flex flex-col gap-4">
        <Link
          to={`/patients/${patientId}/sessions`}
          className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground font-semibold transition-colors w-fit group"
        >
          <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-1" />
          Back to Sessions Log
        </Link>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 select-none">
          <div className="flex flex-col gap-1.5">
            <div className="flex items-center flex-wrap gap-3">
              <h1 className="text-xl font-bold tracking-tight text-foreground">
                Consultation Session Workspace
              </h1>
              
              {isNoteFinalized ? (
                <Badge variant="outline" className="px-2.5 py-0.5 rounded-full text-[10px] font-bold border-emerald-500/20 bg-emerald-500/10 text-emerald-400 select-none flex items-center gap-1">
                  <CheckCircle2 className="h-3 w-3" />
                  Finalized
                </Badge>
              ) : session?.note ? (
                <Badge variant="outline" className="px-2.5 py-0.5 rounded-full text-[10px] font-bold border-amber-500/20 bg-amber-500/10 text-amber-400 select-none flex items-center gap-1 animate-pulse">
                  <AlertTriangle className="h-3 w-3" />
                  Draft Review
                </Badge>
              ) : (
                <Badge variant="outline" className="px-2.5 py-0.5 rounded-full text-[10px] font-bold border-white/10 bg-white/[0.04] text-muted-foreground select-none">
                  Pending Audio Recording
                </Badge>
              )}
            </div>
            
            {isLoading ? (
              <Skeleton className="h-4 w-44" />
            ) : (
              <span className="text-xs font-semibold text-muted-foreground">
                Patient: <strong className="text-foreground">{patient?.name}</strong> · Session ID: #{sessionId?.slice(0, 8).toUpperCase()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── Unified Workspace Layout Grid ──────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 select-none">
        
        {/* ── Left Column (Audio + Transcript) ──────────────────── */}
        <div className="flex flex-col gap-6 select-none">
          
          {/* Audio Wave Recorder Panel */}
          <Card className="border border-white/[0.06] bg-slate-900/40 shadow-lg rounded-2xl overflow-hidden relative">
            <CardHeader className="border-b border-white/[0.06] py-4">
              <CardTitle className="text-sm font-bold tracking-wide text-foreground">
                Audio Recorder Workspace
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 flex flex-col items-center justify-center gap-5 select-none">
              
              {/* Visualized Wave / Status Block */}
              <div className="w-full h-24 rounded-2xl bg-white/[0.01] border border-white/[0.04] flex flex-col items-center justify-center gap-2 relative overflow-hidden select-none">
                
                {/* Visual Sage pulsing waveform loops */}
                {isRecording && (
                  <div className="absolute inset-0 flex items-center justify-center gap-1 opacity-25 select-none">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
                      <span
                        key={i}
                        className="w-1 rounded-full bg-[#508a7b] animate-bounce shrink-0"
                        style={{
                          height: `${Math.floor(Math.random() * 40) + 10}px`,
                          animationDuration: `${Math.floor(Math.random() * 600) + 400}ms`,
                        }}
                      />
                    ))}
                  </div>
                )}

                <span className={cn('text-2xl font-mono select-none tracking-wider', isRecording ? 'text-rose-400 font-bold' : 'text-foreground')}>
                  {formatRecordingTime(recordingSeconds)}
                </span>
                
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                  {isRecording ? 'Capturing consultation audio stream...' : 'Microphone idle'}
                </span>
              </div>

              {/* Action Buttons Toolbar */}
              <div className="flex items-center gap-3 select-none">
                {!isRecording ? (
                  <button
                    type="button"
                    onClick={startRecording}
                    disabled={isNoteFinalized}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-[#508a7b] hover:bg-[#437568] active:bg-[#396358] text-white shadow-md transition-all active:scale-[0.98] disabled:opacity-50"
                  >
                    <Mic className="h-4 w-4 fill-current" />
                    Record Consultation
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={stopRecording}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-rose-500/10 border border-rose-500/20 text-rose-400 hover:bg-rose-500/20 shadow-md transition-all active:scale-[0.98]"
                  >
                    <Square className="h-4 w-4 fill-current" />
                    Stop Capturing
                  </button>
                )}

                {recordedBlob && !isRecording && (
                  <button
                    type="button"
                    onClick={handleUploadAudio}
                    disabled={uploadAudioMutation.isPending || isNoteFinalized}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] active:scale-[0.98] text-foreground transition-all disabled:opacity-50"
                  >
                    <Volume2 className="h-4 w-4 text-muted-foreground" />
                    {uploadAudioMutation.isPending ? 'Transcribing...' : 'Upload & Transcribe'}
                  </button>
                )}
              </div>

            </CardContent>
          </Card>

          {/* Transcript Viewer Panel */}
          <Card className="border border-white/[0.06] bg-slate-900/40 shadow-lg rounded-2xl overflow-hidden flex flex-col flex-1">
            <CardHeader className="border-b border-white/[0.06] flex flex-row items-center justify-between py-4 select-none">
              <CardTitle className="text-sm font-bold tracking-wide text-foreground">
                Raw Transcript Text Viewer
              </CardTitle>

              {session?.transcript && (
                <button
                  type="button"
                  onClick={handleCopyTranscript}
                  className="p-1.5 rounded-lg hover:bg-white/[0.04] text-muted-foreground hover:text-foreground transition-all shrink-0"
                  title="Copy transcript"
                >
                  <Copy className="h-4 w-4" />
                </button>
              )}
            </CardHeader>
            <CardContent className="p-6 flex flex-col gap-5 flex-1 select-none">
              
              <div className="flex-1 min-h-[220px] max-h-[360px] overflow-y-auto rounded-2xl border border-white/[0.04] bg-black/10 p-4 relative select-text">
                {isLoading ? (
                  <div className="space-y-2 select-none">
                    <Skeleton className="h-4 w-full animate-pulse" />
                    <Skeleton className="h-4 w-5/6 animate-pulse" />
                    <Skeleton className="h-4 w-4/5 animate-pulse" />
                  </div>
                ) : !session?.transcript ? (
                  <div className="absolute inset-0 flex flex-col items-center justify-center text-xs text-muted-foreground select-none italic text-center p-4">
                    No transcript generated. Speak into the microphone and upload or await processed records.
                  </div>
                ) : (
                  <p className="text-xs font-medium text-foreground/90 leading-relaxed whitespace-pre-wrap select-text">
                    {session.transcript}
                  </p>
                )}
              </div>

              {session?.transcript && !isNoteFinalized && (
                <button
                  type="button"
                  onClick={handleGenerateNote}
                  disabled={generateNoteMutation.isPending}
                  className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-[#508a7b] hover:bg-[#437568] active:bg-[#396358] text-white shadow-md active:scale-[0.98] transition-all disabled:opacity-50 select-none"
                >
                  <Sparkles className="h-4 w-4 fill-current animate-pulse" />
                  {generateNoteMutation.isPending ? 'Generating SOAP Draft...' : 'Generate SOAP Notes Draft'}
                </button>
              )}

            </CardContent>
          </Card>

        </div>

        {/* ── Right Column (SOAP Editor + Summary) ────────────────── */}
        <div className="flex flex-col gap-6 select-none">
          
          {/* AI Session Summary Card */}
          {renderSummaryCard()}

          {/* SOAP Note Tabbed Form Editor */}
          <Card className="border border-white/[0.06] bg-slate-900/40 shadow-lg rounded-2xl overflow-hidden flex-1 flex flex-col">
            <CardHeader className="border-b border-white/[0.06] flex flex-col gap-3 py-4 select-none">
              <div className="flex items-center justify-between gap-4">
                <CardTitle className="text-sm font-bold tracking-wide text-foreground">
                  SOAP Clinical Notes Editor
                </CardTitle>
                
                {isNoteFinalized && (
                  <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] rounded-full flex items-center gap-1 select-none">
                    <Lock className="h-3 w-3 shrink-0" />
                    Locked
                  </Badge>
                )}
              </div>

              {/* Horizontal Tabs selector */}
              <Tabs
                value={soapTab}
                onValueChange={(v) => setSoapTab(v as any)}
                className="w-full"
              >
                <TabsList className="bg-white/[0.02] border border-white/[0.06] w-full p-1 rounded-xl grid grid-cols-4 select-none">
                  <TabsTrigger value="subjective" className="text-[10px] font-bold uppercase tracking-wider py-1.5 rounded-lg active:scale-95 transition-all">S</TabsTrigger>
                  <TabsTrigger value="objective" className="text-[10px] font-bold uppercase tracking-wider py-1.5 rounded-lg active:scale-95 transition-all">O</TabsTrigger>
                  <TabsTrigger value="assessment" className="text-[10px] font-bold uppercase tracking-wider py-1.5 rounded-lg active:scale-95 transition-all">A</TabsTrigger>
                  <TabsTrigger value="plan" className="text-[10px] font-bold uppercase tracking-wider py-1.5 rounded-lg active:scale-95 transition-all">P</TabsTrigger>
                </TabsList>
              </Tabs>
            </CardHeader>
            <CardContent className="p-6 flex-1 flex flex-col gap-5 select-none justify-between">
              
              <div className="flex-1 flex flex-col gap-4">
                
                {soapTab === 'subjective' && (
                  <div className="flex flex-col gap-4 animate-in fade-in duration-200">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                        Presenting Complaint
                      </label>
                      <textarea
                        value={noteState.presenting_complaint}
                        disabled={isNoteFinalized || isLoading}
                        onChange={(e) => setNoteState({ ...noteState, presenting_complaint: e.target.value })}
                        placeholder="Enter the patient's subjective symptoms and history..."
                        className="w-full h-24 text-xs font-semibold p-3.5 rounded-xl border border-white/[0.06] bg-black/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#508a7b] disabled:opacity-50 select-text leading-relaxed"
                      />
                    </div>
                    
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                        Symptoms Mentioned (Comma separated)
                      </label>
                      <textarea
                        value={symptomsText}
                        disabled={isNoteFinalized || isLoading}
                        onChange={(e) => setSymptomsText(e.target.value)}
                        placeholder="e.g. fatigue, insomnia, anxiety..."
                        className="w-full h-12 text-xs font-semibold p-3.5 rounded-xl border border-white/[0.06] bg-black/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#508a7b] disabled:opacity-50 select-text leading-relaxed"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Mood words</label>
                        <input
                          value={noteState.mood_in_patient_words}
                          disabled={isNoteFinalized || isLoading}
                          onChange={(e) => setNoteState({ ...noteState, mood_in_patient_words: e.target.value })}
                          type="text"
                          className="w-full text-xs font-semibold p-3 rounded-xl border border-white/[0.06] bg-black/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#508a7b] disabled:opacity-50 select-text"
                          placeholder="Patient's words..."
                        />
                      </div>
                      <div className="flex flex-col gap-1.5">
                        <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Sleep Quality</label>
                        <input
                          value={noteState.sleep}
                          disabled={isNoteFinalized || isLoading}
                          onChange={(e) => setNoteState({ ...noteState, sleep: e.target.value })}
                          type="text"
                          className="w-full text-xs font-semibold p-3 rounded-xl border border-white/[0.06] bg-black/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#508a7b] disabled:opacity-50 select-text"
                          placeholder="Sleep duration/quality..."
                        />
                      </div>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Social Context</label>
                      <input
                        value={noteState.social_context}
                        disabled={isNoteFinalized || isLoading}
                        onChange={(e) => setNoteState({ ...noteState, social_context: e.target.value })}
                        type="text"
                        className="w-full text-xs font-semibold p-3 rounded-xl border border-white/[0.06] bg-black/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#508a7b] disabled:opacity-50 select-text"
                        placeholder="Work pressure, support..."
                      />
                    </div>
                  </div>
                )}

                {soapTab === 'objective' && (
                  <div className="flex flex-col gap-4 animate-in fade-in duration-200">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                        Medications Mentioned (Comma separated)
                      </label>
                      <textarea
                        value={medicationsText}
                        disabled={isNoteFinalized || isLoading}
                        onChange={(e) => setMedicationsText(e.target.value)}
                        placeholder="e.g. Sertraline 50mg, Ibuprofen..."
                        className="w-full h-24 text-xs font-semibold p-3.5 rounded-xl border border-white/[0.06] bg-black/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#508a7b] disabled:opacity-50 select-text leading-relaxed"
                      />
                    </div>
                  </div>
                )}

                {soapTab === 'assessment' && (
                  <div className="flex flex-col gap-4 animate-in fade-in duration-200">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                        Clinical Assessment Flags
                      </label>
                      <textarea
                        value={noteState.flags_for_review}
                        disabled={isNoteFinalized || isLoading}
                        onChange={(e) => setNoteState({ ...noteState, flags_for_review: e.target.value })}
                        placeholder="Review flags and diagnostic summaries..."
                        className="w-full h-24 text-xs font-semibold p-3.5 rounded-xl border border-white/[0.06] bg-black/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#508a7b] disabled:opacity-50 select-text leading-relaxed"
                      />
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                        AI Confidence Metric (Read-Only)
                      </label>
                      <input
                        value={noteState.confidence || 'unknown'}
                        disabled
                        type="text"
                        className="w-full text-xs font-bold p-3 rounded-xl border border-white/[0.06] bg-black/10 text-[#508a7b] capitalize select-none cursor-not-allowed opacity-80"
                      />
                    </div>
                  </div>
                )}

                {soapTab === 'plan' && (
                  <div className="flex flex-col gap-4 animate-in fade-in duration-200">
                    <div className="flex flex-col gap-1.5">
                      <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                        Clinical Treatment Plan
                      </label>
                      <textarea
                        value={noteState.plan_discussed}
                        disabled={isNoteFinalized || isLoading}
                        onChange={(e) => setNoteState({ ...noteState, plan_discussed: e.target.value })}
                        placeholder="Discussed therapy routines, medications adjustments, and follow-ups..."
                        className="w-full h-32 text-xs font-semibold p-3.5 rounded-xl border border-white/[0.06] bg-black/10 text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-[#508a7b] disabled:opacity-50 select-text leading-relaxed"
                      />
                    </div>
                  </div>
                )}

              </div>

              {/* SOAP Finalize Trigger */}
              {!isNoteFinalized && (noteState.presenting_complaint || noteState.plan_discussed) && (
                <button
                  type="button"
                  onClick={handleSaveNote}
                  disabled={saveNoteMutation.isPending}
                  className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold bg-[#508a7b] hover:bg-[#437568] active:bg-[#396358] text-white shadow-md active:scale-[0.98] transition-all disabled:opacity-50 select-none mt-4"
                >
                  <CheckCircle2 className="h-4 w-4 fill-current animate-pulse" />
                  {saveNoteMutation.isPending ? 'Finalizing Notes...' : 'Save & Finalize Note'}
                </button>
              )}

            </CardContent>
          </Card>

        </div>

      </div>

    </div>
  );
}
