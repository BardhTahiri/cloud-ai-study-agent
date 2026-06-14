import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  createCourse,
  createStudyTask,
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

  const taskStats = useMemo(() => {
    const completed = tasks.filter((task) => task.status === "completed").length;
    return {
      total: tasks.length,
      completed
    };
  }, [tasks]);

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

      setTasks((current) => [createdTask, ...current]);
      setSelectedTask(createdTask);
      setFile(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate study package.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="workspace">
        <aside className="control-panel">
          <div className="brand-block">
            <span className="eyebrow">Cloud AI Study Agent</span>
            <h1>Study package generator</h1>
          </div>

          <div className="stats-row">
            <div>
              <strong>{taskStats.total}</strong>
              <span>Tasks</span>
            </div>
            <div>
              <strong>{taskStats.completed}</strong>
              <span>Completed</span>
            </div>
          </div>

          {error && <p className="error-text">{error}</p>}

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

            <label htmlFor="file">PDF or text file</label>
            <input
              id="file"
              type="file"
              accept=".pdf,.txt"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />

            <button className="primary-button" disabled={isSubmitting} type="submit">
              {isSubmitting ? "Generating..." : "Generate study package"}
            </button>
          </form>

          <div className="task-list">
            <h2>Recent tasks</h2>
            {tasks.map((task) => (
              <button
                key={task.id}
                className={task.id === selectedTask?.id ? "task-item active" : "task-item"}
                type="button"
                onClick={() => setSelectedTask(task)}
              >
                <span>{task.title}</span>
                <small>{task.status}</small>
              </button>
            ))}
          </div>
        </aside>

        <TaskResult task={selectedTask} />
      </section>
    </main>
  );
}

export default App;
