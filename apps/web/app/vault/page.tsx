"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

type Experience = {
  id: number;
  user_id: string;
  title: string;
  impact: string;
  skills: string[];
  kind: "project" | "internship" | "club" | "volunteering";
};

type StoryCard = {
  id: number;
  headline: string;
  summary: string;
  evidence_points: string[];
  skills: string[];
};

type RetrievalResult = {
  retrieval_audit_id: number;
  cards: StoryCard[];
};

export default function VaultPage() {
  const client = useQueryClient();
  const [form, setForm] = useState({ title: "", impact: "", skills: "Python, SQL", kind: "project" });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedCardIds, setSelectedCardIds] = useState<number[]>([]);
  const [retrievalAuditId, setRetrievalAuditId] = useState<number | null>(null);
  const [jobId, setJobId] = useState("job_1");

  const experiences = useQuery({ queryKey: ["vault", "experience"], queryFn: () => apiFetch<Experience[]>("/vault/experience?user_id=demo-user") });
  const storyCards = useQuery({ queryKey: ["vault", "cards"], queryFn: () => apiFetch<StoryCard[]>("/story-cards?user_id=demo-user") });

  const saveExperience = useMutation({
    mutationFn: async () => {
      const payload = {
        user_id: "demo-user",
        title: form.title,
        impact: form.impact,
        kind: form.kind,
        skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean)
      };
      if (editingId) {
        return apiFetch(`/vault/experience/${editingId}`, { method: "PUT", body: JSON.stringify(payload) });
      }
      return apiFetch("/vault/experience", { method: "POST", body: JSON.stringify(payload) });
    },
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["vault", "experience"] }),
        client.invalidateQueries({ queryKey: ["vault", "cards"] })
      ]);
      setForm({ title: "", impact: "", skills: "Python, SQL", kind: "project" });
      setEditingId(null);
    }
  });

  const deleteExperience = useMutation({
    mutationFn: (id: number) => apiFetch(`/vault/experience/${id}?user_id=demo-user`, { method: "DELETE" }),
    onSuccess: async () => {
      await Promise.all([
        client.invalidateQueries({ queryKey: ["vault", "experience"] }),
        client.invalidateQueries({ queryKey: ["vault", "cards"] })
      ]);
    }
  });

  const retrieveStories = useMutation({
    mutationFn: () =>
      apiFetch<RetrievalResult>("/story-cards/retrieve", {
        method: "POST",
        body: JSON.stringify({ user_id: "demo-user", job_id: jobId, top_k: 3 })
      }),
    onSuccess: (result) => {
      setRetrievalAuditId(result.retrieval_audit_id);
      setSelectedCardIds(result.cards.map((c) => c.id));
    }
  });

  const createDraft = useMutation({
    mutationFn: () =>
      apiFetch<{ id: number; body: string; selected_evidence: string[] }>("/applications/drafts", {
        method: "POST",
        body: JSON.stringify({
          user_id: "demo-user",
          job_id: jobId,
          selected_story_card_ids: selectedCardIds,
          retrieval_audit_id: retrievalAuditId
        })
      })
  });

  const cardsById = useMemo(() => {
    const map = new Map<number, StoryCard>();
    (storyCards.data ?? []).forEach((card) => map.set(card.id, card));
    return map;
  }, [storyCards.data]);

  const toggleSelected = (id: number) => {
    setSelectedCardIds((prev) => (prev.includes(id) ? prev.filter((v) => v !== id) : [...prev, id]));
  };

  return (
    <section className="space-y-4">
      <article className="rounded-xl border p-4">
        <h2 className="text-lg font-semibold">Experience Vault</h2>
        <div className="mt-3 grid gap-2">
          <input className="rounded border p-2 text-sm" placeholder="Experience title" value={form.title} onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))} />
          <textarea className="rounded border p-2 text-sm" placeholder="Impact statement" value={form.impact} onChange={(e) => setForm((f) => ({ ...f, impact: e.target.value }))} />
          <input className="rounded border p-2 text-sm" placeholder="Skills (comma-separated)" value={form.skills} onChange={(e) => setForm((f) => ({ ...f, skills: e.target.value }))} />
          <select className="rounded border p-2 text-sm" value={form.kind} onChange={(e) => setForm((f) => ({ ...f, kind: e.target.value }))}>
            <option value="project">Project</option>
            <option value="internship">Internship</option>
            <option value="club">Club</option>
            <option value="volunteering">Volunteering</option>
          </select>
          <button onClick={() => saveExperience.mutate()} className="rounded bg-brand px-3 py-2 text-sm text-white">{editingId ? "Update experience" : "Add experience"}</button>
        </div>
      </article>

      <article className="rounded-xl border p-4">
        <h3 className="font-semibold">Your experience items</h3>
        <div className="mt-2 space-y-2">
          {experiences.data?.map((item) => (
            <div key={item.id} className="rounded border p-3">
              <p className="font-medium">{item.title}</p>
              <p className="text-sm">{item.impact}</p>
              <p className="text-xs text-slate-500">{item.skills.join(" • ")}</p>
              <div className="mt-2 flex gap-2 text-xs">
                <button
                  className="rounded border px-2 py-1"
                  onClick={() => {
                    setEditingId(item.id);
                    setForm({
                      title: item.title,
                      impact: item.impact,
                      skills: item.skills.join(", "),
                      kind: item.kind
                    });
                  }}
                >
                  Edit
                </button>
                <button className="rounded border px-2 py-1 text-rose-700" onClick={() => deleteExperience.mutate(item.id)}>Delete</button>
              </div>
            </div>
          ))}
        </div>
      </article>

      <article className="rounded-xl border p-4">
        <h3 className="font-semibold">Story Engine Retrieval</h3>
        <p className="text-xs text-slate-500">Boundary: retrieval uses only your story cards and logs an audit id.</p>
        <div className="mt-2 flex gap-2">
          <select className="flex-1 rounded border p-2 text-sm" value={jobId} onChange={(e) => setJobId(e.target.value)}>
            <option value="job_1">job_1</option>
            <option value="job_2">job_2</option>
          </select>
          <button className="rounded bg-brand px-3 py-2 text-sm text-white" onClick={() => retrieveStories.mutate()}>Retrieve</button>
        </div>

        <div className="mt-3 space-y-2">
          {storyCards.data?.map((card) => (
            <label key={card.id} className="block rounded border p-3">
              <div className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={selectedCardIds.includes(card.id)}
                  onChange={() => toggleSelected(card.id)}
                />
                <div>
                  <p className="font-medium">{card.headline}</p>
                  <p className="text-sm text-slate-600">{card.summary}</p>
                  <p className="mt-1 text-xs text-slate-500">Evidence: {card.evidence_points.join(" | ")}</p>
                </div>
              </div>
            </label>
          ))}
        </div>

        <button className="mt-3 w-full rounded bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => createDraft.mutate()}>
          Create application draft with selected evidence
        </button>
        {createDraft.data && (
          <div className="mt-3 rounded bg-emerald-50 p-3 text-sm">
            <p className="font-medium">Draft #{createDraft.data.id}</p>
            <p className="mt-1 whitespace-pre-wrap">{createDraft.data.body}</p>
          </div>
        )}
        {retrievalAuditId && <p className="mt-2 text-xs text-slate-500">Retrieval audit id: {retrievalAuditId}</p>}
      </article>
    </section>
  );
}
