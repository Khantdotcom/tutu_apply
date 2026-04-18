export type Mission = {
  id: string | number;
  title: string;
  xp: number;
  status: "todo" | "done";
};

export type RequirementEvidence = {
  requirement: string;
  evidence: string[];
};

export type FitScoreOutput = {
  score: number;
  confidence: number;
  matched_requirements: RequirementEvidence[];
  missing_skills: string[];
  reasoning: string[];
  evidence_ids: string[];
};

export type ExperienceItem = {
  id: number;
  user_id: string;
  title: string;
  impact: string;
  skills: string[];
  kind: "project" | "internship" | "club" | "volunteering";
};

export type StoryCard = {
  id: number;
  headline: string;
  summary: string;
  evidence_points: string[];
  skills: string[];
};
