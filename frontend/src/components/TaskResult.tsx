import type { StudyTask } from "../types/study";

type TaskResultProps = {
  task: StudyTask | null;
};

export function TaskResult({ task }: TaskResultProps) {
  if (!task) {
    return (
      <section className="result-panel empty-state">
        <p>Generate a study package to see the first AI output here.</p>
      </section>
    );
  }

  if (task.status === "failed") {
    return (
      <section className="result-panel">
        <h2>{task.title}</h2>
        <p className="error-text">{task.error ?? "The study task failed."}</p>
      </section>
    );
  }

  if (!task.result) {
    return (
      <section className="result-panel">
        <h2>{task.title}</h2>
        <p>Task status: {task.status}</p>
      </section>
    );
  }

  return (
    <section className="result-panel">
      <div className="result-header">
        <div>
          <span className="eyebrow">Completed package</span>
          <h2>{task.result.title}</h2>
        </div>
        <span className="status-pill">{task.status}</span>
      </div>

      <div className="section-block">
        <h3>Important Topics</h3>
        <div className="topic-list">
          {task.result.important_topics.map((topic) => (
            <span key={topic} className="topic-pill">
              {topic}
            </span>
          ))}
        </div>
      </div>

      <div className="section-block">
        <h3>Summary</h3>
        <ol className="summary-list">
          {task.result.summary.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </div>

      <div className="section-block">
        <h3>Quiz</h3>
        <div className="quiz-list">
          {task.result.quiz.map((question) => (
            <article key={question.question} className="quiz-card">
              <strong>{question.question}</strong>
              <p>{question.answer}</p>
              <span>{question.topic}</span>
            </article>
          ))}
        </div>
      </div>

      <div className="section-block">
        <h3>Study Plan</h3>
        <div className="plan-grid">
          {task.result.study_plan.map((day) => (
            <article key={day.day} className="plan-card">
              <span>Day {day.day}</span>
              <h4>{day.focus}</h4>
              <ul>
                {day.tasks.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
