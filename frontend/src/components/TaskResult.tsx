import { useEffect, useState } from "react";
import {
  AlertTriangle,
  BookOpenCheck,
  Check,
  CheckCircle2,
  CircleHelp,
  CloudCog,
  FileQuestion,
  Lightbulb,
  ListChecks,
  LoaderCircle,
  Sparkles,
  Target,
  X
} from "lucide-react";

import type { StudyTask } from "../types/study";

type TaskResultProps = {
  task: StudyTask | null;
};

export function TaskResult({ task }: TaskResultProps) {
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    setSelectedAnswers({});
  }, [task?.id]);

  if (!task) {
    return (
      <section className="result-panel empty-state">
        <div className="empty-state-content">
          <div className="empty-illustration" aria-hidden="true">
            <BookOpenCheck size={34} />
            <span><Sparkles size={16} /></span>
          </div>
          <span className="eyebrow">Ready when you are</span>
          <h2>Your study package will appear here</h2>
          <p>Add material on the left to generate a focused summary, interactive quiz, and day-by-day study plan.</p>
          <div className="empty-features" aria-hidden="true">
            <span><Lightbulb size={15} /> Key concepts</span>
            <span><FileQuestion size={15} /> Practice quiz</span>
            <span><ListChecks size={15} /> Study plan</span>
          </div>
        </div>
      </section>
    );
  }

  if (task.status === "failed") {
    return (
      <section className="result-panel">
        <div className="result-header">
          <div>
            <span className="eyebrow">Package generation</span>
            <h2>{task.title}</h2>
          </div>
          <span className="status-pill failed"><AlertTriangle size={14} /> Failed</span>
        </div>
        <div className="failed-state" role="alert">
          <span className="failed-icon"><AlertTriangle size={24} /></span>
          <div>
            <h3>The agent could not finish this package</h3>
            <p>{task.error ?? "The study task failed. Check the worker logs and try again."}</p>
          </div>
        </div>
      </section>
    );
  }

  if (!task.result) {
    const isProcessing = task.status === "processing";

    return (
      <section className="result-panel">
        <div className="result-header">
          <div>
            <span className="eyebrow">Cloud generation</span>
            <h2>{task.title}</h2>
          </div>
          <span className={`status-pill ${task.status}`}>
            <LoaderCircle size={14} className="rotating-icon" />
            {task.status}
          </span>
        </div>

        <div className="processing-state">
          <div className="processing-orbit" aria-hidden="true">
            <CloudCog size={32} />
            <span />
          </div>
          <span className="eyebrow">Background agent active</span>
          <h3>{isProcessing ? "Creating your learning materials" : "Your request is in the queue"}</h3>
          <p>Azure keeps processing if you close this page or turn off this computer. Temporary model outages are retried automatically.</p>

          <div className="progress-block">
            <div className="progress-label">
              <span>{isProcessing ? "Generating package" : "Waiting for worker"}</span>
              <strong>{task.progress}%</strong>
            </div>
            <div className="progress-track" aria-label={`Task progress ${task.progress}%`}>
              <div className="progress-bar" style={{ width: `${task.progress}%` }} />
            </div>
          </div>

          <div className="processing-steps">
            <div className="processing-step complete">
              <CheckCircle2 size={18} />
              <span><strong>Request saved</strong><small>Material stored locally</small></span>
            </div>
            <div className={isProcessing ? "processing-step active" : "processing-step"}>
              {isProcessing ? <LoaderCircle size={18} className="rotating-icon" /> : <span className="step-number">2</span>}
              <span><strong>Agent processing</strong><small>Analyzing important concepts</small></span>
            </div>
            <div className="processing-step">
              <span className="step-number">3</span>
              <span><strong>Package ready</strong><small>Summary, quiz, and plan</small></span>
            </div>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="result-panel">
      <div className="result-header completed-header">
        <div>
          <span className="eyebrow">Completed package</span>
          <h2>{task.result.title}</h2>
          {task.result.generation && (
            <div className="generation-meta">
              <span className={`generation-tier ${task.result.generation.tier}`}>
                {task.result.generation.tier}
              </span>
              <span><CloudCog size={14} /> {task.result.generation.provider}</span>
              <span>{task.result.generation.model}</span>
            </div>
          )}
        </div>
        <span className="status-pill completed"><Check size={14} /> Completed</span>
      </div>

      {task.result.generation?.fallback_reason && (
        <div className="notice-text">
          <AlertTriangle size={17} aria-hidden="true" />
          <span>The configured model was unavailable, so the offline generator completed this package.</span>
        </div>
      )}

      <section className="section-block topics-section">
        <div className="content-heading">
          <span className="content-icon"><Target size={18} /></span>
          <div>
            <span className="eyebrow">Exam focus</span>
            <h3>Important topics</h3>
          </div>
        </div>
        <div className="topic-list">
          {task.result.important_topics.map((topic) => (
            <span key={topic} className="topic-pill">{topic}</span>
          ))}
        </div>
      </section>

      <section className="section-block">
        <div className="content-heading">
          <span className="content-icon"><Lightbulb size={18} /></span>
          <div>
            <span className="eyebrow">Core material</span>
            <h3>Summary</h3>
          </div>
        </div>
        <ol className="summary-list">
          {task.result.summary.map((item, index) => (
            <li key={`${index}-${item}`}>
              <span className="summary-number">{String(index + 1).padStart(2, "0")}</span>
              <p>{item}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="section-block">
        <div className="content-heading split-heading">
          <span className="content-icon"><CircleHelp size={18} /></span>
          <div>
            <span className="eyebrow">Knowledge check</span>
            <h3>Practice quiz</h3>
          </div>
          <span className="section-count">{task.result.quiz.length} questions</span>
        </div>
        <div className="quiz-list">
          {task.result.quiz.map((question, questionIndex) => {
            const options = question.options?.length ? question.options : [question.answer];
            const correctOption = question.correct_option ?? question.answer;
            const selectedAnswer = selectedAnswers[question.question];
            const isCorrect = selectedAnswer === correctOption;

            return (
              <article key={question.question} className="quiz-card">
                <div className="quiz-question-heading">
                  <span>{String(questionIndex + 1).padStart(2, "0")}</span>
                  <div>
                    <small>{question.topic}</small>
                    <h4>{question.question}</h4>
                  </div>
                </div>
                <div className="quiz-options">
                  {options.map((option, optionIndex) => {
                    const isSelected = selectedAnswer === option;
                    const isCorrectOption = Boolean(selectedAnswer) && option === correctOption;
                    const optionClass = [
                      "quiz-option",
                      isSelected ? "selected" : "",
                      isCorrectOption ? "correct" : "",
                      isSelected && !isCorrect ? "wrong" : ""
                    ].filter(Boolean).join(" ");

                    return (
                      <button
                        key={option}
                        className={optionClass}
                        type="button"
                        aria-pressed={isSelected}
                        onClick={() => setSelectedAnswers((current) => ({ ...current, [question.question]: option }))}
                      >
                        <span className="option-letter">{String.fromCharCode(65 + optionIndex)}</span>
                        <span className="option-copy">{option}</span>
                        {isCorrectOption && <Check size={17} className="option-result-icon" aria-hidden="true" />}
                        {isSelected && !isCorrect && <X size={17} className="option-result-icon" aria-hidden="true" />}
                      </button>
                    );
                  })}
                </div>
                {selectedAnswer && (
                  <div className={isCorrect ? "feedback correct-text" : "feedback wrong-text"} role="status">
                    {isCorrect ? <CheckCircle2 size={17} /> : <AlertTriangle size={17} />}
                    <span>{isCorrect ? "Correct. Nice work." : `Not quite. The correct answer is ${correctOption}.`}</span>
                  </div>
                )}
              </article>
            );
          })}
        </div>
      </section>

      <section className="section-block">
        <div className="content-heading split-heading">
          <span className="content-icon"><ListChecks size={18} /></span>
          <div>
            <span className="eyebrow">Your schedule</span>
            <h3>Study plan</h3>
          </div>
          <span className="section-count">{task.result.study_plan.length} days</span>
        </div>
        <div className="plan-grid">
          {task.result.study_plan.map((day) => (
            <article key={day.day} className="plan-card">
              <div className="plan-card-heading">
                <span className="day-number">Day {String(day.day).padStart(2, "0")}</span>
                <Sparkles size={16} aria-hidden="true" />
              </div>
              <h4>{day.focus}</h4>
              <ul>
                {day.tasks.map((item, index) => (
                  <li key={`${index}-${item}`}><Check size={14} aria-hidden="true" /><span>{item}</span></li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
