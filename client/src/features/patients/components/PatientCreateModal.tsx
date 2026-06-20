import { useState } from 'react';
import { useCreatePatient } from '@/features/patients/hooks/useCreatePatient';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { User, Calendar, Phone, Mail } from 'lucide-react';
import Spinner from '@/components/common/Spinner';
import { useNavigate } from 'react-router-dom';

interface PatientCreateModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function PatientCreateModal({ open, onOpenChange }: PatientCreateModalProps) {
  const [name, setName] = useState('');
  const [dateOfBirth, setDateOfBirth] = useState('');
  const [gender, setGender] = useState('other');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');

  const navigate = useNavigate();
  const createMutation = useCreatePatient();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !dateOfBirth) return;

    const dob = new Date(dateOfBirth);
    let age = new Date().getFullYear() - dob.getFullYear();
    const m = new Date().getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && new Date().getDate() < dob.getDate())) {
      age--;
    }

    createMutation.mutate(
      { name, age, gender },
      {
        onSuccess: (newPatient) => {
          onOpenChange(false);
          setName('');
          setDateOfBirth('');
          navigate(`/patients/${newPatient.id}/timeline`);
        },
      }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px] bg-white border-border shadow-lg rounded-xl">
        <DialogHeader>
          <DialogTitle className="text-lg font-bold text-[#191c1d] flex items-center gap-2">
            <User className="h-5 w-5 text-[#003d9b]" />
            New Clinical Profile
          </DialogTitle>
          <DialogDescription className="text-xs font-semibold text-[#747783]">
            Register a new patient into the clinical workspace.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-4">
          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold text-[#747783] tracking-widest">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-2.5 h-4 w-4 text-[#747783]" />
              <input
                required
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. John Doe"
                className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-[#f8f9fa] text-sm text-[#191c1d] focus:outline-none focus:border-[#003d9b] focus:ring-1 focus:ring-[#003d9b] transition-all"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-[#747783] tracking-widest">Date of Birth</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-2.5 h-4 w-4 text-[#747783]" />
                <input
                  required
                  type="date"
                  value={dateOfBirth}
                  onChange={(e) => setDateOfBirth(e.target.value)}
                  className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-[#f8f9fa] text-sm text-[#191c1d] focus:outline-none focus:border-[#003d9b] focus:ring-1 focus:ring-[#003d9b] transition-all"
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-[#747783] tracking-widest">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-border bg-[#f8f9fa] text-sm text-[#191c1d] focus:outline-none focus:border-[#003d9b] focus:ring-1 focus:ring-[#003d9b] transition-all"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold text-[#747783] tracking-widest">Phone Number (Optional)</label>
            <div className="relative">
              <Phone className="absolute left-3 top-2.5 h-4 w-4 text-[#747783]" />
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="(555) 123-4567"
                className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-[#f8f9fa] text-sm text-[#191c1d] focus:outline-none focus:border-[#003d9b] focus:ring-1 focus:ring-[#003d9b] transition-all"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold text-[#747783] tracking-widest">Email Address (Optional)</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-[#747783]" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="patient@example.com"
                className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-[#f8f9fa] text-sm text-[#191c1d] focus:outline-none focus:border-[#003d9b] focus:ring-1 focus:ring-[#003d9b] transition-all"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="text-[#747783] border-border hover:bg-[#f8f9fa] font-bold"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isPending}
              className="bg-[#003d9b] hover:bg-[#00296d] text-white shadow-sm font-bold w-24"
            >
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
