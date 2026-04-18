"use client";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { FitRing } from "@/components/fit-ring";

type Job = { id: string; title: string; company: string; location: string; requirements: string[]; fit_score?: number };

export default function JobsPage() {
  const client = useQueryClient();
  const jobs = useQuery({ queryKey: ["jobs"], queryFn: () => apiFetch<Job[]>("/jobs?user_id=demo-user") });
  const saveJob = useMutation({
    mutationFn: (jobId: string) => apiFetch(`/jobs/${jobId}/save`, { method: "POST", body: JSON.stringify({ user_id: "demo-user" }) }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["jobs"] })
  });

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Job opportunities</h2>
      {jobs.data?.map((job) => (
        <article key={job.id} className="rounded-xl border p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-semibold">{job.title}</h3>
              <p className="text-sm text-slate-600">{job.company} • {job.location}</p>
            </div>
            <FitRing score={job.fit_score ?? 0} />
          </div>
          <p className="mt-2 text-xs">Requirements: {job.requirements.join(", ")}</p>
          <div className="mt-3 flex items-center justify-between">
            <Link href={`/jobs/${job.id}`} className="text-sm font-medium text-brand">View details</Link>
            <button onClick={() => saveJob.mutate(job.id)} className="rounded bg-brand px-3 py-1 text-sm text-white">Save</button>
          </div>
        </article>
      ))}
    </section>
  );
}
