import { type FormEvent, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  BookOpenCheck,
  CheckCircle2,
  Cloud,
  FileText,
  Layers3,
  Plus,
  Sparkles,
  Trash2,
  UploadCloud,
  X
} from "lucide-react";

import {
  createCourse,
  createStudyTask,
  deleteStudyTask,
  getStudyTask,
  listCourses,
  listStudyTasks,
  uploadStudyMaterial
} from "./api/client";
import { TaskResult } from "./components/TaskResult";
import type { Course, StudyTask } from "./types/study";

const sampleMaterial =
  "Cloud computing provides on-demand access to shared computing resources such as servers, storage, databases, networking, and software. It allows applications to scale based on demand and reduces the need for local infrastructure. A cloud-based AI study agent can process academic materials in the background, store task progress, and generate summaries, quizzes, and study plans even when the user closes the browser. Important concepts include cloud storage, background workers, queues, databases, monitoring, and AI-generated learning support.";

function formatTaskDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function App() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [tasks, setTasks] = useState<StudyTask[]>([]);
  const [selectedTask, setSelectedTask] = useState<StudyTask | null>(null);
  const [courseId, setCourseId] = useState("");
  const [newCourseName, setNewCourseName] = useState("");
  const [title, setTitle] = useState("Cloud Computing Study Package");
  const [prompt, setPrompt] = useState("Focus on the most important concepts for exam preparation.");
  const [materialText, setMaterialText] = useState(sampleMaterial);
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([listCourses(), listStudyTasks()])
      .then(([courseData, taskData]) => {
        setCourses(courseData);
        setTasks(taskData);
        setCourseId(courseData[0]?.id ?? "");
        setSelectedTask(taskData[0] ?? null);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedTask || !["pending", "processing"].includes(selectedTask.status)) {
      return;
    }

    const timer = window.setInterval(() => {
      getStudyTask(selectedTask.id)
        .then((updatedTask) => {
          setSelectedTask(updatedTask);
          upsertTask(updatedTask);
        })
        .catch((err: Error) => setError(err.message));
    }, 1200);

    return () => window.clearInterval(timer);
  }, [selectedTask?.id, selectedTask?.status]);

  const taskStats = useMemo(() => {
    const completed = tasks.filter((task) => task.status === "completed").length;
    const active = tasks.filter((task) => ["pending", "processing"].includes(task.status)).length;
    return { total: tasks.length, completed, active };
  }, [tasks]);

  function upsertTask(updatedTask: StudyTask) {
    setTasks((current) => {
      const exists = current.some((task) => task.id === updatedTask.id);
      if (!exists) return [updatedTask, ...current];
      return current.map((task) => (task.id === updatedTask.id ? updatedTask : task));
    });
  }

  async function handleCreateCourse(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!newCourseName.trim()) return;

    try {
      setError("");
      const course = await createCourse({
        name: newCourseName,
        description: "Created from the study dashboard."
      });
      setCourses((current) => [...current, course]);
      setCourseId(course.id);
      setNewCourseName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create course.");
    }
  }

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      const createdTask = file
        ? await uploadStudyMaterial({ file, title, prompt, courseId: courseId || undefined })
        : await createStudyTask({
            title,
            prompt,
            course_id: courseId || undefined,
            material_text: materialText,
            source_type: "text"
          });

      upsertTask(createdTask);
      setSelectedTask(createdTask);
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate study package.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteTask(taskId: string) {
    try {
      setError("");
      await deleteStudyTask(taskId);
      setTasks((current) => {
        const nextTasks = current.filter((task) => task.id !== taskId);
        if (selectedTask?.id === taskId) setSelectedTask(nextTasks[0] ?? null);
        return nextTasks;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove task.");
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="app-brand">
          <span className="brand-mark" aria-hidden="true">
            <BookOpenCheck size={23} strokeWidth={2.2} />
          </span>
          <div>
            <span className="product-kicker">AI learning workspace</span>
            <h1>Cloud Study Agent</h1>
          </div>
        </div>

        <div className="header-status">
          <span className="mode-badge">
            <span className="status-dot" aria-hidden="true" />
            Hybrid agent mode
          </span>
          <div className="architecture-label">
            <Cloud size={18} aria-hidden="true" />
            <span>
              <small>Architecture</small>
              Local data + Azure AI
            </span>
          </div>
        </div>
      </header>

      <section className="workspace">
        <aside className="control-panel">
          <div className="panel-intro">
            <div className="section-icon" aria-hidden="true">
              <Sparkles size={18} />
            </div>
            <div>
              <span className="eyebrow">New package</span>
              <h2>Build your study session</h2>
              <p>Turn course material into an exam-ready package.</p>
            </div>
          </div>

          <div className="stats-row" aria-label="Study task overview">
            <div className="stat-item">
              <Layers3 size={17} aria-hidden="true" />
              <span><strong>{taskStats.total}</strong> Total</span>
            </div>
            <div className="stat-item">
              <Activity size={17} aria-hidden="true" />
              <span><strong>{taskStats.active}</strong> Running</span>
            </div>
            <div className="stat-item">
              <CheckCircle2 size={17} aria-hidden="true" />
              <span><strong>{taskStats.completed}</strong> Done</span>
            </div>
          </div>

          {error && (
            <div className="error-text" role="alert">
              <AlertCircle size={17} aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          <section className="panel-section course-section">
            <div className="section-heading">
              <div>
                <span className="section-label">Course library</span>
                <p>Group packages by subject.</p>
              </div>
            </div>
            <form className="inline-form" onSubmit={handleCreateCourse}>
              <label className="visually-hidden" htmlFor="new-course">New course name</label>
              <div className="inline-row">
                <input
                  id="new-course"
                  value={newCourseName}
                  onChange={(event) => setNewCourseName(event.target.value)}
                  placeholder="Add a new course"
                />
                <button className="icon-text-button" type="submit" disabled={!newCourseName.trim()}>
                  <Plus size={17} aria-hidden="true" />
                  Add
                </button>
              </div>
            </form>
          </section>

          <section className="panel-section generator-section">
            <div className="section-heading">
              <div>
                <span className="section-label">Package details</span>
                <p>Choose a course, goal, and source material.</p>
              </div>
            </div>
            <form className="study-form" onSubmit={handleGenerate}>
              <div className="field-group">
                <label htmlFor="course">Course</label>
                <select id="course" value={courseId} onChange={(event) => setCourseId(event.target.value)}>
                  <option value="">No course selected</option>
                  {courses.map((course) => (
                    <option key={course.id} value={course.id}>{course.name}</option>
                  ))}
                </select>
              </div>

              <div className="field-group">
                <label htmlFor="title">Study package title</label>
                <input id="title" value={title} onChange={(event) => setTitle(event.target.value)} required />
              </div>

              <div className="field-group">
                <label htmlFor="prompt">Learning goal</label>
                <textarea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={3} required />
              </div>

              <div className="field-group">
                <label htmlFor="material">Material text</label>
                <textarea
                  id="material"
                  value={materialText}
                  onChange={(event) => setMaterialText(event.target.value)}
                  rows={7}
                  disabled={Boolean(file)}
                  required={!file}
                />
                <span className="field-hint">Paste text here or upload a PDF below.</span>
              </div>

              <div className="field-group">
                <span className="input-label">Source file</span>
                <label className={file ? "file-drop has-file" : "file-drop"} htmlFor="file">
                  <UploadCloud size={21} aria-hidden="true" />
                  <span className="file-drop-copy">
                    <strong>{file ? "File ready to process" : "Upload PDF or text"}</strong>
                    <small>{file ? file.name : "PDF or TXT, one file at a time"}</small>
                  </span>
                  <span className="file-action">Browse</span>
                </label>
                <input
                  className="visually-hidden"
                  id="file"
                  type="file"
                  accept=".pdf,.txt"
                  onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                />
              </div>

              {file && (
                <div className="selected-file">
                  <FileText size={16} aria-hidden="true" />
                  <span>{file.name}</span>
                  <button type="button" onClick={() => setFile(null)} aria-label={`Clear ${file.name}`} title="Clear file">
                    <X size={16} aria-hidden="true" />
                  </button>
                </div>
              )}

              <button className="primary-button" disabled={isSubmitting} type="submit">
                {isSubmitting ? (
                  <span className="button-loading">
                    <span className="button-spinner" aria-hidden="true" />
                    Sending to agent...
                  </span>
                ) : (
                  <>
                    <Sparkles size={18} aria-hidden="true" />
                    Generate study package
                  </>
                )}
              </button>
            </form>
          </section>

          <section className="panel-section recent-section">
            <div className="section-heading task-heading">
              <div>
                <span className="section-label">Recent packages</span>
                <p>Saved in your local database.</p>
              </div>
              <span className="count-badge">{tasks.length}</span>
            </div>
            <div className="task-list">
              {tasks.length === 0 && <p className="empty-list">No study packages yet.</p>}
              {tasks.map((task) => (
                <div key={task.id} className={task.id === selectedTask?.id ? "task-row active" : "task-row"}>
                  <button className="task-item" type="button" onClick={() => setSelectedTask(task)}>
                    <span className={`task-status-dot ${task.status}`} aria-hidden="true" />
                    <span className="task-copy">
                      <strong>{task.title}</strong>
                      <small>{task.status} · {formatTaskDate(task.created_at)}</small>
                    </span>
                  </button>
                  <button
                    aria-label={`Remove ${task.title}`}
                    title="Remove task"
                    className="remove-task-button"
                    type="button"
                    onClick={() => handleDeleteTask(task.id)}
                  >
                    <Trash2 size={16} aria-hidden="true" />
                  </button>
                </div>
              ))}
            </div>
          </section>
        </aside>

        <TaskResult task={selectedTask} />
      </section>
    </main>
  );
}

export default App;
