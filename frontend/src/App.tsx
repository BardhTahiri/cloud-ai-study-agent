import { FormEvent, useEffect, useMemo, useState } from "react";

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
    return {
      total: tasks.length,
      completed,
      active
    };
  }, [tasks]);

  function upsertTask(updatedTask: StudyTask) {
    setTasks((current) => {
      const exists = current.some((task) => task.id === updatedTask.id);
      if (!exists) {
        return [updatedTask, ...current];
      }
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
        description: "Created from the demo dashboard."
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
        ? await uploadStudyMaterial({
            file,
            title,
            prompt,
            courseId: courseId || undefined
          })
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
        if (selectedTask?.id === taskId) {
          setSelectedTask(nextTasks[0] ?? null);
        }
        return nextTasks;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not remove task.");
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <span className="eyebrow">Academic AI workspace</span>
          <h1>Cloud AI Study Agent</h1>
          <p>Generate summaries, quizzes, important topics, and study plans from your own material.</p>
        </div>
        <div className="database-badge">
          <span>Hybrid architecture</span>
          <strong>Local data, cloud AI agent</strong>
        </div>
      </header>

      <section className="workspace">
        <aside className="control-panel">
          <div className="brand-block">
            <span className="eyebrow">Study workflow</span>
            <h1>Study package generator</h1>
          </div>

          <div className="stats-row">
            <div>
              <strong>{taskStats.total}</strong>
              <span>Tasks</span>
            </div>
            <div>
              <strong>{taskStats.active}</strong>
              <span>Running</span>
            </div>
            <div>
              <strong>{taskStats.completed}</strong>
              <span>Completed</span>
            </div>
          </div>

          {error && <p className="error-text">{error}</p>}

          <section className="panel-section">
            <div className="section-heading">
              <h2>Create course</h2>
              <p>Group generated study packages by subject.</p>
            </div>
            <form className="inline-form" onSubmit={handleCreateCourse}>
              <label htmlFor="new-course">New course</label>
              <div className="inline-row">
                <input
                  id="new-course"
                  value={newCourseName}
                  onChange={(event) => setNewCourseName(event.target.value)}
                  placeholder="e.g. Artificial Intelligence"
                />
                <button type="submit">Add</button>
              </div>
            </form>
          </section>

          <section className="panel-section">
            <div className="section-heading">
              <h2>Generate package</h2>
              <p>Paste text or upload a file, then let the worker build the study output.</p>
            </div>
            <form className="study-form" onSubmit={handleGenerate}>
              <label htmlFor="course">Course</label>
              <select id="course" value={courseId} onChange={(event) => setCourseId(event.target.value)}>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))}
              </select>

              <label htmlFor="title">Study package title</label>
              <input id="title" value={title} onChange={(event) => setTitle(event.target.value)} />

              <label htmlFor="prompt">Prompt</label>
              <textarea id="prompt" value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={3} />

              <label htmlFor="material">Material text</label>
              <textarea
                id="material"
                value={materialText}
                onChange={(event) => setMaterialText(event.target.value)}
                rows={9}
                disabled={Boolean(file)}
              />
              <p className="field-hint">When a file is selected, the uploaded file will be used instead of pasted text.</p>

              <label htmlFor="file">PDF or text file</label>
              <input
                id="file"
                type="file"
                accept=".pdf,.txt"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              />
              {file && (
                <div className="selected-file">
                  <span>{file.name}</span>
                  <button type="button" onClick={() => setFile(null)}>
                    Clear
                  </button>
                </div>
              )}

              <button className="primary-button" disabled={isSubmitting} type="submit">
                {isSubmitting ? (
                  <span className="button-loading">
                    <span className="button-spinner" aria-hidden="true" />
                    Generating...
                  </span>
                ) : (
                  "Generate study package"
                )}
              </button>
            </form>
          </section>

          <section className="panel-section">
            <div className="section-heading">
              <h2>Recent tasks</h2>
              <p>Stored in the database and available after refresh.</p>
            </div>
            <div className="task-list">
              {tasks.length === 0 && <p className="empty-list">No study tasks yet.</p>}
              {tasks.map((task) => (
                <div key={task.id} className={task.id === selectedTask?.id ? "task-row active" : "task-row"}>
                  <button className="task-item" type="button" onClick={() => setSelectedTask(task)}>
                    <span>{task.title}</span>
                    <small>{task.status}</small>
                  </button>
                  <button
                    aria-label={`Remove ${task.title}`}
                    className="remove-task-button"
                    type="button"
                    onClick={() => handleDeleteTask(task.id)}
                  >
                    Remove
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
