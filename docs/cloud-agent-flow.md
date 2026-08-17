# Hybrid Cloud Agent Flow

The student application and permanent database remain local. Only AI generation runs in Azure.

```text
1. Student uploads a PDF or submits text to the local backend.
2. The local backend extracts PDF text and stores the study task locally.
3. The backend sends title, prompt, and extracted text to the cloud agent API over HTTPS.
4. The agent API places the material on Redis and returns a cloud job ID.
5. The cloud worker generates the summary, quiz, important topics, and study plan.
6. Redis keeps the job status and result temporarily.
7. The local backend checks the cloud job when the frontend polls the local task.
8. The completed result is copied into the local database for permanent access.
```

The original PDF and the local database are not deployed to Azure. Agent results expire from Redis after seven days by default, so the local application should synchronize completed jobs within that window.

The cloud API requires `X-Agent-API-Key` when `AGENT_API_KEY` is configured. Always configure a strong key in Azure.
