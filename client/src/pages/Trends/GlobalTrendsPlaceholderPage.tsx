import { useNavigate } from 'react-router-dom';
import { TrendingUp, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function GlobalTrendsPlaceholderPage() {
  const navigate = useNavigate();

  return (
    <div className="max-w-md mx-auto min-h-[70vh] flex flex-col items-center justify-center p-6 text-center">
      <div className="bg-white border border-[#E2E8E4] rounded-2xl shadow-sm p-8 flex flex-col items-center">
        <div className="h-16 w-16 rounded-full bg-[#466551]/10 flex items-center justify-center text-[#466551] mb-6">
          <TrendingUp className="h-8 w-8" />
        </div>
        <h1 className="text-lg font-bold text-[#1a1c1a] mb-2">Biomarker Trends</h1>
        <p className="text-xs text-[#424843] leading-relaxed mb-6">
          Longitudinal biomarker tracking, vitals visualization, and AI trend synthesis require patient-level clinical contexts.
          Please select a patient from the directory to review vitals trends.
        </p>
        <Button
          onClick={() => navigate('/patients')}
          className="w-full bg-[#466551] hover:bg-[#3b5443] text-white font-bold h-10 rounded-lg flex items-center justify-center gap-2 text-xs"
        >
          <span>View Patient Directory</span>
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
