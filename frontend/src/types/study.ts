export type Course = {
  id: string;
  name: string;
  description: string;
  created_at: string;
};

export type QuizQuestion = {
  question: string;
  answer: string;
  topic: string;
  options?: string[];
  correct_option?: string;
};

export type StudyPlanDay = {
  day: number;
  focus: string;
  tasks: string[];
};

export type StudyResult = {
  title: string;
  important_topics: string[];
  summary: string[];
  quiz: QuizQuestion[];
  study_plan: StudyPlanDay[];
  generation?: {
    tier: "offline" | "free" | "codex";
    provider: string;
    model: string;
    fallback_reason?: string | null;
  };
};

export type StudyTask = {
  id: string;
  title: string;
  course_id: string | null;
  prompt: string;
  source_type: string;
  source_name: string | null;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  result: StudyResult | null;
  error: string | null;
  created_at: string;
  updated_at: string;
};

export type StudyTaskPayload = {
  title: string;
  course_id?: string;
  prompt: string;
  material_text: string;
  source_type: "prompt" | "text" | "pdf";
  source_name?: string;
};
