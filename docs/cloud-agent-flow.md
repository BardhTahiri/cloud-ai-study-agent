# Cloud Agent Flow

The cloud-based agent should process study tasks independently from the user's browser session.

```text
1. Student uploads material or submits a prompt.
2. Backend stores the request.
3. Backend creates an agent task.
4. Task is sent to the queue.
5. Worker receives the task.
6. Worker extracts and analyzes the content.
7. Worker generates summary, quiz, and study plan.
8. Results are stored.
9. Student views the completed outputs later.
```
