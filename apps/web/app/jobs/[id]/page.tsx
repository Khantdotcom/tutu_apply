"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { FitRing } from "@/components/fit-ring";

type MatchedRequirement = { requirement: string; evidence: string[] };
type FitPreview = {
  score: number;
  confidence: number;
  matched_requirements: MatchedRequirement[];
  missing_skills: string[];
  reasoning: string[];
};

type StoryCard = { id: number; headline: string; evidence_points: string[] };


type JobDetail = {
  id: string;
  title: string;
  company: string;
  location: string;
  requirements: string[];
  fit_score?: number;
  fit_preview?: FitPreview;
};

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const client = useQueryClient();
  const [applicationId, setApplicationId] = useState<number | null>(null);
  const [selectedStoryCardIds, setSelectedStoryCardIds] = useState<number[]>([]);
  const [question, setQuestion] = useState("Why are you a fit for this role?");

  const { data } = useQuery({
    queryKey: ["job", params.id],
    queryFn: () => apiFetch<JobDetail>(`/jobs/${params.id}?user_id=demo-user`)
  });

  const stories = useQuery({
    queryKey: ["story-cards"],
    queryFn: () => apiFetch<StoryCard[]>("/story-cards?user_id=demo-user")
  });

  const history = useQuery({
    queryKey: ["generation-history", applicationId],
    queryFn: () => apiFetch<any[]>(`/applications/${applicationId}/history?user_id=demo-user`),
    enabled: Boolean(applicationId)
  });

  const createApplication = useMutation({
    mutationFn: () => apiFetch<{ id: number }>("/applications", { method: "POST", body: JSON.stringify({ user_id: "demo-user", job_id: params.id }) }),
    onSuccess: (result) => setApplicationId(result.id)
  });

  const generateCover = useMutation({
    mutationFn: () =>
      apiFetch(`/applications/${applicationId}/generate-cover-letter`, {
        method: "POST",
        body: JSON.stringify({ user_id: "demo-user", selected_story_card_ids: selectedStoryCardIds })
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["generation-history", applicationId] })
  });

  const generateShort = useMutation({
    mutationFn: () =>
      apiFetch(`/applications/${applicationId}/generate-short-answer`, {
        method: "POST",
        body: JSON.stringify({
          user_id: "demo-user",
          question,
          selected_story_card_ids: selectedStoryCardIds
        })
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["generation-history", applicationId] })
  });

  useEffect(() => {
    if (stories.data && selectedStoryCardIds.length === 0) {
      setSelectedStoryCardIds(stories.data.slice(0, 2).map((s) => s.id));
    }
  }, [stories.data, selectedStoryCardIds.length]);

  if (!data) return <p>Loading job...</p>;

  return (
    <section className="space-y-4">
      <header className="rounded-xl border p-4">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">{data.title}</h2>
            <p className="text-sm text-slate-600">{data.company} • {data.location}</p>
          </div>
          <FitRing score={data.fit_score ?? 0} />
        </div>
      </header>

      <article className="rounded-xl border p-4">
        <h3 className="font-semibold">Matched requirements</h3>
        <div className="mt-2 space-y-2">
          {data.fit_preview?.matched_requirements.map((match) => (
            <div key={match.requirement} className="rounded border bg-emerald-50 p-2 text-sm">
              <p className="font-medium">{match.requirement}</p>
              <p className="text-xs text-slate-700">Evidence: {match.evidence.join(" • ")}</p>
            </div>
          ))}
        </div>
      </article>

      <article className="rounded-xl border p-4">
        <h3 className="font-semibold">Application Generator MVP</h3>
        {!applicationId ? (
          <button onClick={() => createApplication.mutate()} className="mt-2 rounded bg-brand px-3 py-2 text-sm text-white">
            Create application from saved job
          </button>
        ) : (
          <p className="mt-2 text-sm text-emerald-700">Application #{applicationId} created.</p>
        )}

        <div className="mt-3 space-y-2">
          <p className="text-xs text-slate-500">Select evidence stories (evidence-only writing enforced):</p>
          {stories.data?.map((story) => (
            <label key={story.id} className="block rounded border p-2 text-sm">
              <input
                type="checkbox"
                className="mr-2"
                checked={selectedStoryCardIds.includes(story.id)}
                onChange={() =>
                  setSelectedStoryCardIds((prev) =>
                    prev.includes(story.id) ? prev.filter((id) => id !== story.id) : [...prev, story.id]
                  )
                }
              />
              {story.headline}
            </label>
          ))}
        </div>

        <div className="mt-3 grid gap-2">
          <button
            disabled={!applicationId}
            onClick={() => generateCover.mutate()}
            className="rounded bg-brand px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            Generate cover letter draft
          </button>

          <input
            className="rounded border p-2 text-sm"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Short-answer question"
          />
          <button
            disabled={!applicationId}
            onClick={() => generateShort.mutate()}
            className="rounded bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            Generate short-answer draft
          </button>
        </div>
      </article>

      <article className="rounded-xl border p-4">
        <h3 className="font-semibold">Generation history / status</h3>
        <div className="mt-2 space-y-2 text-sm">
          {history.data?.map((item) => (
            <div key={item.id} className="rounded border p-2">
              <p className="font-medium">{item.run_type} • {item.status}</p>
              <p className="text-xs text-slate-500">Artifact: {item.artifact_type ?? "n/a"}</p>
            </div>
          ))}
          {!history.data?.length && <p className="text-xs text-slate-500">No generation runs yet.</p>}
        </div>
      </article>
    </section>
  );
}
