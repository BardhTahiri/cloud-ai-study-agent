# Azure Agent Deployment

Only the agent API, worker, and queue are deployed to Azure.

## Current Deployment

The following resources are provisioned in `cloud-ai-study-rg`:

```text
Region:          Germany West Central
Registry:        cloudaistudyrg.azurecr.io
Agent image:     cloud-ai-agent:v5 (live) / v6 (Codex migration target)
Managed Redis:   cloud-ai-agent-redis
Redis SKU:       Balanced_B0 (high availability disabled for development)
Redis endpoint:  cloud-ai-agent-redis.germanywestcentral.redis.azure.net:10000
```

Provider checkpoint (2026-08-20): Groq free mode is configured and verified with `openai/gpt-oss-20b` using strict JSON Schema output. The repository now replaces the paid OpenAI API adapter with a ChatGPT-authenticated Codex subscription adapter. The live v5 worker must remain on Groq until v6 is built, a persistent auth mount is attached, and Codex login is completed.

The Redis database uses encrypted transport, access-key authentication, and the `NoCluster` policy required by the Celery/Kombu queue. The access key and complete `REDIS_URL` must be stored as Container Apps secrets and must not be committed.

## Components

```text
Local backend
    -> HTTPS agent API (Azure Container Apps, external ingress)
    -> Azure Managed Redis
    -> Celery worker (Azure Container Apps, no ingress)
    -> selected LLM endpoint
```

## Build The Agent Image

The existing `cloud-ai-backend:v1` image can remain in the registry, but the hybrid architecture uses the smaller standalone agent image:

```powershell
az acr build --registry cloudaistudyrg --image cloud-ai-agent:v2 --file worker/Dockerfile .
```

Both Container Apps use:

```text
cloudaistudyrg.azurecr.io/cloud-ai-agent:v2
```

The API uses the image's default command. The worker overrides it with:

```text
celery -A worker.app.celery_app:celery_app worker --loglevel=info
```

## Environment Contract

Agent API:

```env
REDIS_URL=<Azure Managed Redis TLS URL>
AGENT_API_KEY=<strong shared secret>
AGENT_RESULT_EXPIRES_SECONDS=604800
```

Worker:

```env
REDIS_URL=<same Azure Managed Redis TLS URL>
AGENT_RESULT_EXPIRES_SECONDS=604800
LLM_BASE_URL=<empty, codex://subscription, or compatible endpoint>
LLM_API_KEY=<compatible-provider key>
FREE_LLM_MODEL=qwen3:8b
CODEX_MODEL=gpt-5.6-sol
CODEX_BIN=codex
CODEX_HOME=/codex-auth
CODEX_TIMEOUT_SECONDS=300
LLM_MAX_INPUT_CHARS=100000
FREE_LLM_MAX_INPUT_CHARS=12000
```

Local backend after deployment:

```env
TASK_QUEUE_MODE=cloud
TASK_QUEUE_FALLBACK_LOCAL=false
AGENT_BASE_URL=https://<agent-api-fqdn>
AGENT_API_KEY=<same shared secret>
```

Keep secrets out of tracked files and configure them as Container Apps secrets.

## Complete The Deployment Manually

Run these commands from PowerShell in the repository root. Keep the same PowerShell window open because later commands reuse the variables. Commands marked **slow** can take several minutes.

### 1. Set deployment variables

```powershell
$ResourceGroup = "cloud-ai-study-rg"
$Location = "germanywestcentral"
$Environment = "cloud-ai-agent-env"
$Registry = "cloudaistudyrg"
$Image = "cloudaistudyrg.azurecr.io/cloud-ai-agent:v2"
$Identity = "cloud-ai-agent-pull-id"
$ApiApp = "cloud-ai-agent-api"
$WorkerApp = "cloud-ai-agent-worker"
$RedisName = "cloud-ai-agent-redis"
$RedisHost = "cloud-ai-agent-redis.germanywestcentral.redis.azure.net"
```

### 2. Prepare Container Apps

```powershell
az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
```

The two provider registration commands can be slow. Verify both return `Registered`:

```powershell
az provider show --namespace Microsoft.App --query registrationState --output tsv
az provider show --namespace Microsoft.OperationalInsights --query registrationState --output tsv
```

### 3. Create the Container Apps environment

**Slow:**

```powershell
az containerapp env create --name $Environment --resource-group $ResourceGroup --location $Location
```

Verify:

```powershell
az containerapp env show --name $Environment --resource-group $ResourceGroup --query "{name:name,state:properties.provisioningState,location:location}" --output table
```

### 4. Create one image-pull identity

```powershell
az identity create --name $Identity --resource-group $ResourceGroup --location $Location
$IdentityId = az identity show --name $Identity --resource-group $ResourceGroup --query id --output tsv
$PrincipalId = az identity show --name $Identity --resource-group $ResourceGroup --query principalId --output tsv
$AcrId = az acr show --name $Registry --query id --output tsv
az role assignment create --assignee-object-id $PrincipalId --assignee-principal-type ServicePrincipal --role AcrPull --scope $AcrId
```

Role propagation can take a minute. Verify:

```powershell
az role assignment list --assignee $PrincipalId --scope $AcrId --query "[].roleDefinitionName" --output table
```

### 5. Build the in-memory secrets

These variables are not written to the repository:

```powershell
$RedisKey = az redisenterprise database list-keys --cluster-name $RedisName --resource-group $ResourceGroup --query primaryKey --output tsv
$EncodedRedisKey = [System.Uri]::EscapeDataString($RedisKey)
$RedisUrl = "rediss://:$EncodedRedisKey@${RedisHost}:10000/0?ssl_cert_reqs=required"
$AgentApiKey = ([guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N"))
```

Do not print, screenshot, or commit `$RedisKey`, `$RedisUrl`, or `$AgentApiKey`.

### 6. Deploy the agent API

**Slow:**

```powershell
az containerapp create --name $ApiApp --resource-group $ResourceGroup --environment $Environment --image $Image --ingress external --target-port 8010 --transport http --min-replicas 0 --max-replicas 1 --cpu 0.25 --memory 0.5Gi --user-assigned $IdentityId --registry-server "$Registry.azurecr.io" --registry-identity $IdentityId --secrets "redis-url=$RedisUrl" "agent-api-key=$AgentApiKey" --env-vars "REDIS_URL=secretref:redis-url" "AGENT_API_KEY=secretref:agent-api-key" "AGENT_RESULT_EXPIRES_SECONDS=604800"
```

Get and test its public URL:

```powershell
$AgentFqdn = az containerapp show --name $ApiApp --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv
$AgentUrl = "https://$AgentFqdn"
Invoke-RestMethod "$AgentUrl/health"
```

Expected health response:

```text
status  service
ok      cloud-study-agent
```

### 7. Deploy the background worker

The worker has no ingress. It uses one minimum replica so it can receive Redis jobs reliably.

**Slow:**

```powershell
az containerapp create --name $WorkerApp --resource-group $ResourceGroup --environment $Environment --image $Image --min-replicas 1 --max-replicas 1 --cpu 0.5 --memory 1Gi --user-assigned $IdentityId --registry-server "$Registry.azurecr.io" --registry-identity $IdentityId --secrets "redis-url=$RedisUrl" --env-vars "REDIS_URL=secretref:redis-url" "AGENT_RESULT_EXPIRES_SECONDS=604800" --command "celery" --args "-A" "worker.app.celery_app:celery_app" "worker" "--loglevel=info"
```

This initially uses the offline deterministic generator because no `LLM_BASE_URL` is configured. The work still runs in Azure, which makes it suitable for verifying the cloud boundary before adding an API key.

### 8. Verify both Container Apps

```powershell
az containerapp list --resource-group $ResourceGroup --query "[].{name:name,state:properties.provisioningState,fqdn:properties.configuration.ingress.fqdn}" --output table
az containerapp logs show --name $WorkerApp --resource-group $ResourceGroup --tail 50
```

Both apps should show `Succeeded`. Worker logs should include a Celery connection to Azure Managed Redis.

### 9. Run a direct cloud job

```powershell
$Headers = @{ "X-Agent-API-Key" = $AgentApiKey }
$Body = @{ title = "Azure verification"; prompt = "Focus on cloud processing"; material_text = "The local application sends extracted study material to an Azure agent API. Redis queues the task and a Celery worker generates a summary, quiz, important topics, and study plan in the cloud." } | ConvertTo-Json
$Job = Invoke-RestMethod -Method Post -Uri "$AgentUrl/jobs" -Headers $Headers -ContentType "application/json" -Body $Body
$Job
```

Wait a few seconds, then retrieve the result:

```powershell
Invoke-RestMethod -Method Get -Uri "$AgentUrl/jobs/$($Job.job_id)" -Headers $Headers
```

The final status should be `completed` with progress `100`.

### 10. Connect the local backend

Open the ignored local `.env` file and set:

```env
TASK_QUEUE_MODE=cloud
TASK_QUEUE_FALLBACK_LOCAL=false
AGENT_BASE_URL=https://<the value stored in $AgentFqdn>
AGENT_API_KEY=<the value stored in $AgentApiKey>
```

Use the clipboard without printing the secret:

```powershell
$AgentUrl | Set-Clipboard
$AgentApiKey | Set-Clipboard
```

After updating `.env`, restart the local backend. The frontend and permanent database remain local; generated tasks now run through Azure.

## Activate The Codex Subscription

Codex subscription mode is a process running inside the worker, not an HTTP API. It reuses a ChatGPT login stored in `auth.json` and consumes the account's Codex allowance. Keep this private behind the existing agent API key.

First return the live v5 worker to the verified Groq provider so it cannot call the removed paid API configuration:

```powershell
az containerapp update --name cloud-ai-agent-worker --resource-group cloud-ai-study-rg --set-env-vars "LLM_BASE_URL=https://api.groq.com/openai/v1" "FREE_LLM_MODEL=openai/gpt-oss-20b" "FREE_LLM_MAX_INPUT_CHARS=12000" "LLM_FALLBACK_TO_OFFLINE=true"
```

Build the Codex-capable image manually from the repository root:

```powershell
az acr build --registry cloudaistudyrg --image cloud-ai-agent:v6 --file worker/Dockerfile .
```

### Create persistent authentication storage

The refreshed login cache must survive revisions. Create a small Azure Files share in the Container Apps region and link it to the existing environment:

```powershell
$CodexStorageAccount = "cloudaicodex$((Get-Random -Minimum 1000 -Maximum 9999))"
$CodexShare = "codex-auth"
$CodexMount = "codex-auth-storage"

az storage account create --resource-group cloud-ai-study-rg --name $CodexStorageAccount --location swedencentral --kind StorageV2 --sku Standard_LRS
az storage share-rm create --resource-group cloud-ai-study-rg --storage-account $CodexStorageAccount --name $CodexShare --quota 1 --enabled-protocols SMB
$CodexStorageKey = az storage account keys list --resource-group cloud-ai-study-rg --account-name $CodexStorageAccount --query "[0].value" --output tsv
az containerapp env storage set --name cloud-ai-agent-env --resource-group cloud-ai-study-rg --storage-name $CodexMount --access-mode ReadWrite --azure-file-account-name $CodexStorageAccount --azure-file-account-key $CodexStorageKey --azure-file-share-name $CodexShare
```

Do not print or save `$CodexStorageKey`. Azure Container Apps requires a YAML update to attach the environment storage to an existing app. Export the worker definition to a temporary file:

```powershell
$WorkerYaml = Join-Path $env:TEMP "cloud-ai-agent-worker-codex.yaml"
az containerapp show --name cloud-ai-agent-worker --resource-group cloud-ai-study-rg --output yaml | Set-Content -LiteralPath $WorkerYaml -Encoding utf8
notepad $WorkerYaml
```

Remove the exported `properties.configuration.secrets` section so unchanged secrets are not deleted. Under the existing worker container add `volumeMounts`, and under `properties.template` replace `volumes: null` with:

```yaml
containers:
- name: cloud-ai-agent-worker
  volumeMounts:
  - volumeName: codex-auth-volume
    mountPath: /codex-auth
volumes:
- name: codex-auth-volume
  storageName: codex-auth-storage
  storageType: AzureFile
```

Preserve the container's existing image, command, environment, and resource fields, then apply the file:

```powershell
az containerapp update --name cloud-ai-agent-worker --resource-group cloud-ai-study-rg --yaml $WorkerYaml
```

### Deploy and authenticate Codex

Deploy v6, remove the legacy paid-provider variables, and select subscription mode. Keep fallback enabled until login succeeds:

```powershell
az containerapp update --name cloud-ai-agent-worker --resource-group cloud-ai-study-rg --image cloudaistudyrg.azurecr.io/cloud-ai-agent:v6 --remove-env-vars OPENAI_API_KEY PAID_LLM_MODEL OPENAI_REASONING_EFFORT OPENAI_MAX_OUTPUT_TOKENS --set-env-vars "LLM_BASE_URL=codex://subscription" "CODEX_MODEL=gpt-5.6-sol" "CODEX_BIN=codex" "CODEX_HOME=/codex-auth" "CODEX_TIMEOUT_SECONDS=300" "LLM_MAX_INPUT_CHARS=100000" "LLM_FALLBACK_TO_OFFLINE=true"
```

Wait for the revision to become healthy. Open an interactive process in the worker and complete device login in your browser:

```powershell
az containerapp exec --name cloud-ai-agent-worker --resource-group cloud-ai-study-rg --command "codex login --device-auth"
az containerapp exec --name cloud-ai-agent-worker --resource-group cloud-ai-study-rg --command "codex login status"
```

Submit one small package and confirm generation metadata reads `codex`, `chatgpt-codex`, and `gpt-5.6-sol`. After verification, the unused OpenAI API secret can be removed:

```powershell
az containerapp secret remove --name cloud-ai-agent-worker --resource-group cloud-ai-study-rg --secret-names openai-api-key
```

To return to Groq at any time:

```powershell
az containerapp update --name cloud-ai-agent-worker --resource-group cloud-ai-study-rg --set-env-vars "LLM_BASE_URL=https://api.groq.com/openai/v1" "FREE_LLM_MODEL=openai/gpt-oss-20b" "FREE_LLM_MAX_INPUT_CHARS=12000" "LLM_FALLBACK_TO_OFFLINE=true"
```

## Cost Control

The worker's minimum replica is billable while it stays at `1`. Pause worker compute when not testing:

```powershell
az containerapp update --name $WorkerApp --resource-group $ResourceGroup --min-replicas 0
```

Resume before submitting jobs:

```powershell
az containerapp update --name $WorkerApp --resource-group $ResourceGroup --min-replicas 1
```

With no event scale rule, a worker at zero replicas cannot wake itself. Azure Managed Redis also continues its base charge until the Redis resource is deleted.
