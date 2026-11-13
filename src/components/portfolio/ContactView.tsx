import React, { useState } from 'react';
import {
  AlertCircle,
  ArrowUpRight,
  CheckCircle2,
  Github,
  Linkedin,
  Mail,
  Send,
  Youtube,
} from 'lucide-react';
import { PublicProfileDTO } from '../../types';
import { SERVICES_LIST } from '../../data/workbenchData';
import { submitPublicContact } from '../../lib/api/portfolio';

interface ContactViewProps {
  profile: PublicProfileDTO;
}

export const ContactView: React.FC<ContactViewProps> = ({ profile }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [honeypot, setHoneypot] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await submitPublicContact({
        name: name.trim(),
        email: email.trim(),
        subject: subject.trim(),
        message: message.trim(),
        honeypot,
      });
      if (res.received) {
        setSuccessMsg(res.message || 'Message received.');
        setName('');
        setEmail('');
        setSubject('');
        setMessage('');
      }
    } catch (err: any) {
      setError(err?.message || 'Unable to send message right now.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-16 space-y-14">
      <header className="space-y-3 max-w-2xl">
        <div className="text-xs font-mono text-[#00D4FF]">Direct Contact &amp; Channels</div>
        <h1 className="text-3xl sm:text-4xl font-bold font-display text-white [text-wrap:balance]">
          Let&apos;s Work Together
        </h1>
        <p className="text-sm sm:text-base text-slate-400">
          {profile.collaboration_status}. Share technical context below or reach out through verified public channels.
        </p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-start">
        {/* Left: Rate-Limited Honeypot-Protected Contact Form */}
        <div className="lg:col-span-7 p-6 sm:p-8 bg-[#0F172A] border border-slate-800 rounded-lg space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <h2 className="text-lg font-bold font-display text-white">Send an Inquiry</h2>
            <span className="text-xs font-mono text-slate-500">Rate Limit: 3/hour</span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Hidden Honeypot Anti-Spam Field */}
            <div className="hidden" aria-hidden="true">
              <label htmlFor="contact-company-website">Website</label>
              <input
                id="contact-company-website"
                type="text"
                name="website"
                tabIndex={-1}
                autoComplete="off"
                value={honeypot}
                onChange={(e) => setHoneypot(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label htmlFor="contact-name" className="block text-xs font-mono text-slate-300">
                  Name
                </label>
                <input
                  id="contact-name"
                  type="text"
                  required
                  minLength={2}
                  maxLength={120}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your name"
                  className="w-full px-3.5 py-2.5 bg-[#0A0F1E] border border-slate-800 focus:border-[#00D4FF]/60 focus:outline-none rounded text-sm text-white"
                />
              </div>

              <div className="space-y-1.5">
                <label htmlFor="contact-email" className="block text-xs font-mono text-slate-300">
                  Email
                </label>
                <input
                  id="contact-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  className="w-full px-3.5 py-2.5 bg-[#0A0F1E] border border-slate-800 focus:border-[#00D4FF]/60 focus:outline-none rounded text-sm text-white"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label htmlFor="contact-subject" className="block text-xs font-mono text-slate-300">
                Subject
              </label>
              <input
                id="contact-subject"
                type="text"
                required
                minLength={3}
                maxLength={200}
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="AI architecture role, RAG advisory, or system design inquiry"
                className="w-full px-3.5 py-2.5 bg-[#0A0F1E] border border-slate-800 focus:border-[#00D4FF]/60 focus:outline-none rounded text-sm text-white"
              />
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs font-mono">
                <label htmlFor="contact-message" className="text-slate-300">
                  Message
                </label>
                <span className="text-slate-500 tabular-nums">{message.length}/1000</span>
              </div>
              <textarea
                id="contact-message"
                required
                minLength={5}
                maxLength={1000}
                rows={5}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Outline the system goals, constraints, or role details..."
                className="w-full p-3.5 bg-[#0A0F1E] border border-slate-800 focus:border-[#00D4FF]/60 focus:outline-none rounded text-sm text-white leading-relaxed"
              />
            </div>

            {error && (
              <div className="p-3 bg-[#0A0F1E] border border-rose-500/40 rounded flex items-start gap-2 text-xs text-rose-300">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {successMsg && (
              <div className="p-3 bg-[#0A0F1E] border border-emerald-500/40 rounded flex items-start gap-2 text-xs text-emerald-300">
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{successMsg}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-xs font-mono font-semibold bg-[#00D4FF] text-[#0A0F1E] hover:bg-[#38BDF8] disabled:opacity-50 rounded transition-colors whitespace-nowrap shrink-0"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{submitting ? 'Submitting...' : 'Submit Inquiry'}</span>
            </button>
          </form>
        </div>

        {/* Right: Verified Channels & What I Work On */}
        <div className="lg:col-span-5 space-y-6">
          <section className="p-6 bg-[#0F172A] border border-slate-800 rounded-lg space-y-4">
            <h2 className="text-base font-bold font-display text-white flex items-center gap-2">
              <Mail className="w-4 h-4 text-[#00D4FF]" />
              <span>Available Channels</span>
            </h2>
            <div className="space-y-2.5 text-sm">
              <a
                href={profile.social_links.linkedin}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-[#0A0F1E] border border-slate-800 hover:border-[#00D4FF]/40 rounded transition-colors"
              >
                <span className="flex items-center gap-2.5 text-slate-200">
                  <Linkedin className="w-4 h-4 text-[#00D4FF]" />
                  <span>LinkedIn Profile</span>
                </span>
                <ArrowUpRight className="w-4 h-4 text-slate-400" />
              </a>
              <a
                href={profile.social_links.github}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-[#0A0F1E] border border-slate-800 hover:border-[#00D4FF]/40 rounded transition-colors"
              >
                <span className="flex items-center gap-2.5 text-slate-200">
                  <Github className="w-4 h-4 text-[#00D4FF]" />
                  <span>GitHub Repositories</span>
                </span>
                <ArrowUpRight className="w-4 h-4 text-slate-400" />
              </a>
              <a
                href={profile.social_links.youtube}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-[#0A0F1E] border border-slate-800 hover:border-[#00D4FF]/40 rounded transition-colors"
              >
                <span className="flex items-center gap-2.5 text-slate-200">
                  <Youtube className="w-4 h-4 text-rose-400" />
                  <span>AI Engineering YouTube Series</span>
                </span>
                <ArrowUpRight className="w-4 h-4 text-slate-400" />
              </a>
            </div>
          </section>

          <section className="p-6 bg-[#0F172A] border border-slate-800 rounded-lg space-y-4">
            <h2 className="text-base font-bold font-display text-white">What I Work On</h2>
            <ul className="space-y-2.5">
              {SERVICES_LIST.map((svc) => (
                <li key={svc.id} className="text-xs text-slate-300 flex items-start gap-2">
                  <span className="font-mono text-[#00D4FF] shrink-0">{svc.number}.</span>
                  <span>{svc.title}</span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
};
