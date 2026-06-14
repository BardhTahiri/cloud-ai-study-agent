import type { Course, StudyTask, StudyTaskPayload } from "../types/study";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function listCourses(): Promise<Course[]> {
  return request<Course[]>("/courses");
}

export function createCourse(payload: Pick<Course, "name" | "description">): Promise<Course> {
  return request<Course>("/courses", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function listStudyTasks(): Promise<StudyTask[]> {
  return request<StudyTask[]>("/study-tasks");
}

export function getStudyTask(taskId: string): Promise<StudyTask> {
  return request<StudyTask>(`/study-tasks/${taskId}`);
}

export function createStudyTask(payload: StudyTaskPayload): Promise<StudyTask> {
  return request<StudyTask>("/study-tasks", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function deleteStudyTask(taskId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/study-tasks/${taskId}`, {
    method: "DELETE"
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Delete failed with status ${response.status}`);
  }
}

export async function uploadStudyMaterial(payload: {
  file: File;
  title: string;
  prompt: string;
  courseId?: string;
}): Promise<StudyTask> {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("title", payload.title);
  formData.append("prompt", payload.prompt);
  if (payload.courseId) {
    formData.append("course_id", payload.courseId);
  }

  const response = await fetch(`${API_BASE_URL}/study-tasks/upload`, {
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Upload failed with status ${response.status}`);
  }

  return response.json() as Promise<StudyTask>;
}
