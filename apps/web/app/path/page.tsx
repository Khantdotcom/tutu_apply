"use client";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { Mission } from "@tutu/shared";

type PathResponse = {
  chapter: string;
  daily_quest: string;
  missions: Mission[];
  level: number;
  xp: number;
  streak_days: number;
};

export default function PathPage() {
  const { data } = useQuery({
    queryKey: ["path"],
    queryFn: () => apiFetch<PathResponse>("/path?user_id=demo-user")
  });

  return (
    <section className="space-y-4">
      <div className="rounded-xl bg-indigo-50 p-4">
        <p className="text-xs uppercase text-indigo-700">Current chapter</p>
        <h2 className="text-lg font-bold">{data?.chapter ?? "Loading chapter..."}</h2>
        <p className="mt-1 text-sm">Daily quest: {data?.daily_quest ?? "..."}</p>
        <p className="mt-2 text-xs text-indigo-700">Level {data?.level ?? 1} • {data?.xp ?? 0} XP • 🔥 {data?.streak_days ?? 0}</p>
      </div>
      {data?.missions.map((mission) => (
        <article key={mission.id} className="rounded-xl border p-4">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">{mission.title}</h3>
            <span className="text-xs text-xp">+{mission.xp} XP</span>
          </div>
          <p className="mt-2 text-xs uppercase text-slate-500">{mission.status}</p>
        </article>
      ))}
    </section>
  );
}
