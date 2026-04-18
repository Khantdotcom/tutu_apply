"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

type FormState = {
  user_id: string;
  target_role: string;
  career_stage: string;
  preferred_industries: string;
  preferred_locations: string;
  daily_commitment_minutes: string;
};

export default function OnboardingPage() {
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [form, setForm] = useState<FormState>({
    user_id: "demo-user",
    target_role: "Junior Backend Engineer",
    career_stage: "Student",
    preferred_industries: "SaaS, EdTech",
    preferred_locations: "Remote, New York",
    daily_commitment_minutes: "30"
  });

  const update = (key: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const finish = async () => {
    try {
      setError(null);
      const body = new FormData();
      Object.entries(form).forEach(([key, value]) => body.append(key, value));
      if (resumeFile) {
        body.append("resume", resumeFile);
      }
      await apiFetch("/onboarding/complete", {
        method: "POST",
        body
      });
      setDone(true);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <section className="space-y-4 rounded-xl border p-4">
      <h2 className="text-lg font-semibold">Onboarding</h2>
      <p className="text-sm text-slate-600">Set your target and unlock your first chapter.</p>

      <label className="block text-sm">
        Target role
        <input className="mt-1 w-full rounded border p-2" value={form.target_role} onChange={(e) => update("target_role", e.target.value)} />
      </label>

      <label className="block text-sm">
        Career stage
        <select className="mt-1 w-full rounded border p-2" value={form.career_stage} onChange={(e) => update("career_stage", e.target.value)}>
          <option>Student</option>
          <option>Recent Graduate</option>
          <option>Career Switcher</option>
        </select>
      </label>

      <label className="block text-sm">
        Preferred industries (comma-separated)
        <input className="mt-1 w-full rounded border p-2" value={form.preferred_industries} onChange={(e) => update("preferred_industries", e.target.value)} />
      </label>

      <label className="block text-sm">
        Preferred locations (comma-separated)
        <input className="mt-1 w-full rounded border p-2" value={form.preferred_locations} onChange={(e) => update("preferred_locations", e.target.value)} />
      </label>

      <label className="block text-sm">
        Daily commitment (minutes)
        <input type="number" min={10} max={180} className="mt-1 w-full rounded border p-2" value={form.daily_commitment_minutes} onChange={(e) => update("daily_commitment_minutes", e.target.value)} />
      </label>

      <label className="block text-sm">
        Resume upload
        <input type="file" accept=".pdf,.doc,.docx" className="mt-1 w-full rounded border p-2" onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)} />
      </label>

      <button onClick={finish} className="w-full rounded bg-brand px-3 py-2 text-sm text-white">Complete onboarding</button>

      {done && <p className="text-sm text-emerald-700">Onboarding complete. Chapter unlocked.</p>}
      {error && <p className="text-sm text-rose-700">{error}</p>}
    </section>
  );
}
