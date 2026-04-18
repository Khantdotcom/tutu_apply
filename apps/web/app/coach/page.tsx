"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

type Application = { id: number; job_id: string; status: string };
type CoachPlan = {
  id: number;
  duration_days: number;
  progress_pct: number;
  missions: { id: number; title: string; mission_type: string; day_number: number; status: "todo" | "done" }[];
};

export default function CoachPage() {
  const client = useQueryClient();
  const [selectedApplicationId, setSelectedApplicationId] = useState<number | null>(null);

  const unlock = useQuery({ queryKey: ["coach-unlock"], queryFn: () => apiFetch<{ unlocked: boolean; reason: string }>("/coach/unlock-status?user_id=demo-user") });
  const apps = useQuery({ queryKey: ["applications"], queryFn: () => apiFetch<Application[]>("/applications?user_id=demo-user") });
  const plans = useQuery({
    queryKey: ["coach-plans", selectedApplicationId],
    queryFn: () => apiFetch<CoachPlan[]>(`/coach/readiness-plans?user_id=demo-user${selectedApplicationId ? `&application_id=${selectedApplicationId}` : ""}`)
  });

  const create7 = useMutation({
    mutationFn: () =>
      apiFetch("/coach/readiness-plans", {
        method: "POST",
        body: JSON.stringify({ user_id: "demo-user", application_id: selectedApplicationId, duration_days: 7 })
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["coach-plans"] })
  });

  const create14 = useMutation({
    mutationFn: () =>
      apiFetch("/coach/readiness-plans", {
        method: "POST",
        body: JSON.stringify({ user_id: "demo-user", application_id: selectedApplicationId, duration_days: 14 })
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["coach-plans"] })
  });

  const toggleMission = useMutation({
    mutationFn: ({ id, status }: { id: number; status: "todo" | "done" }) =>
      apiFetch(`/coach/readiness-missions/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ user_id: "demo-user", status })
      }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["coach-plans"] })
  });

  return (
    <section className="space-y-4">
      <article className="rounded-xl border p-4">
        <h2 className="text-lg font-semibold">Readiness Coach</h2>
        <p className="mt-1 text-sm text-slate-600">
          {unlock.data?.unlocked
            ? "Coach unlocked. Build your plan from a saved/submitted application."
            : "Coach locked. Save or submit an application to unlock."}
        </p>
      </article>

      <article className="rounded-xl border p-4">
        <h3 className="font-semibold">Target application</h3>
        <select
          className="mt-2 w-full rounded border p-2 text-sm"
          onChange={(e) => setSelectedApplicationId(Number(e.target.value))}
          value={selectedApplicationId ?? ""}
        >
          <option value="">Select application</option>
          {apps.data?.map((app) => (
            <option key={app.id} value={app.id}>
              #{app.id} • {app.job_id} • {app.status}
            </option>
          ))}
        </select>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <button
            disabled={!unlock.data?.unlocked || !selectedApplicationId}
            onClick={() => create7.mutate()}
            className="rounded bg-brand px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            Generate 7-day plan
          </button>
          <button
            disabled={!unlock.data?.unlocked || !selectedApplicationId}
            onClick={() => create14.mutate()}
            className="rounded bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-50"
          >
            Generate 14-day plan
          </button>
        </div>
      </article>

      {plans.data?.map((plan) => (
        <article key={plan.id} className="rounded-xl border p-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold">Plan #{plan.id} • {plan.duration_days}-day</h3>
            <span className="text-sm font-medium text-brand">{plan.progress_pct}%</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded bg-slate-100">
            <div className="h-full bg-brand" style={{ width: `${plan.progress_pct}%` }} />
          </div>
          <div className="mt-3 space-y-2">
            {plan.missions.map((mission) => (
              <label key={mission.id} className="flex items-start gap-2 rounded border p-2 text-sm">
                <input
                  type="checkbox"
                  checked={mission.status === "done"}
                  onChange={(e) => toggleMission.mutate({ id: mission.id, status: e.target.checked ? "done" : "todo" })}
                />
                <div>
                  <p className="font-medium">Day {mission.day_number}: {mission.title}</p>
                  <p className="text-xs text-slate-500">{mission.mission_type}</p>
                </div>
              </label>
            ))}
          </div>
        </article>
      ))}
    </section>
  );
}
