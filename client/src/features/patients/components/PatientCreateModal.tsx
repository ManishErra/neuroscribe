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
  const [error, setError] = useState('');

  const navigate = useNavigate();
  const createMutation = useCreatePatient();

  const todayStr = new Date().toISOString().split('T')[0];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Patient name is required.');
      return;
    }

    if (!dateOfBirth) {
      setError('Date of birth is required.');
      return;
    }

    const dob = new Date(dateOfBirth);
    const today = new Date();

    if (dob > today) {
      setError('Date of Birth cannot be in the future.');
      return;
    }

    const birthYear = dob.getFullYear();
    if (birthYear < 1900 || birthYear > today.getFullYear()) {
      setError('Please enter a realistic year of birth (1900 or later).');
      return;
    }

    let age = today.getFullYear() - dob.getFullYear();
    const m = today.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
      age--;
    }

    if (age < 1 || age > 120) {
      setError('Calculated age must be between 1 and 120 years.');
      return;
    }

    createMutation.mutate(
      { name: name.trim(), age, gender },
      {
        onSuccess: (newPatient) => {
          onOpenChange(false);
          setName('');
          setDateOfBirth('');
          setGender('other');
          setPhone('');
          setEmail('');
          setError('');
          navigate(`/patients/${newPatient.id}/timeline`);
        },
        onError: (err: any) => {
          setError(err.response?.data?.detail || err.message || 'Failed to create patient profile.');
        }
      }
    );
  };

  const handleClose = () => {
    setName('');
    setDateOfBirth('');
    setGender('other');
    setPhone('');
    setEmail('');
    setError('');
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={(val) => { if (!val) handleClose(); else onOpenChange(val); }}>
      <DialogContent className="sm:max-w-[425px] bg-white border-border shadow-lg rounded-xl">
        <DialogHeader>
          <DialogTitle className="text-lg font-bold text-[#191c1d] dark:text-foreground flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            New Clinical Profile
          </DialogTitle>
          <DialogDescription className="text-xs font-semibold text-[#747783] dark:text-muted-foreground">
            Register a new patient into the clinical workspace.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          {error && (
            <div className="bg-rose-50 border border-rose-100 text-rose-800 text-xs font-semibold rounded-lg p-2.5 select-none animate-in fade-in duration-200">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold text-[#747783] dark:text-muted-foreground tracking-widest">Full Name</label>
            <div className="relative">
              <User className="absolute left-3 top-2.5 h-4 w-4 text-[#747783]" />
              <input
                required
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. John Doe"
                className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-[#f8f9fa] dark:bg-muted text-sm text-[#191c1d] dark:text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-[#747783] dark:text-muted-foreground tracking-widest">Date of Birth</label>
              <div className="relative">
                <Calendar className="absolute left-3 top-2.5 h-4 w-4 text-[#747783]" />
                <input
                  required
                  type="date"
                  min="1900-01-01"
                  max={todayStr}
                  value={dateOfBirth}
                  onChange={(e) => setDateOfBirth(e.target.value)}
                  className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-[#f8f9fa] dark:bg-muted text-sm text-[#191c1d] dark:text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                />
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-[10px] uppercase font-bold text-[#747783] dark:text-muted-foreground tracking-widest">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full h-9 px-3 rounded-md border border-border bg-[#f8f9fa] dark:bg-muted text-sm text-[#191c1d] dark:text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold text-[#747783] dark:text-muted-foreground tracking-widest">Phone Number (Optional)</label>
            <div className="relative">
              <Phone className="absolute left-3 top-2.5 h-4 w-4 text-[#747783]" />
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="(555) 123-4567"
                className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-[#f8f9fa] dark:bg-muted text-sm text-[#191c1d] dark:text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[10px] uppercase font-bold text-[#747783] dark:text-muted-foreground tracking-widest">Email Address (Optional)</label>
            <div className="relative">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-[#747783]" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="patient@example.com"
                className="w-full h-9 pl-9 pr-3 rounded-md border border-border bg-[#f8f9fa] dark:bg-muted text-sm text-[#191c1d] dark:text-foreground focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
              />
            </div>
          </div>

          <div className="pt-2 flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              className="text-[#747783] border-border hover:bg-[#f8f9fa] dark:hover:bg-muted/10 font-bold"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={createMutation.isPending}
              className="bg-primary hover:opacity-90 text-white shadow-sm font-bold w-24"
            >
              {createMutation.isPending ? <Spinner size="sm" /> : 'Create'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
