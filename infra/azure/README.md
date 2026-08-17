# Azure Agent Deployment

Only the agent API, worker, and queue are deployed to Azure.

## Current Deployment

The following resources are provisioned in `cloud-ai-study-rg`:

```text
Region:          Germany West Central
Registry:        cloudaistudyrg.azurecr.io
Agent image:     cloud-ai-agent:v2
Managed Redis:   cloud-ai-agent-redis
Redis SKU:       Balanced_B0 (high availability disabled for development)
Redis endpoint:  cloud-ai-agent-redis.germanywestcentral.redis.azure.net:10000
```

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
LLM_BASE_URL=<empty, OpenAI, or compatible endpoint>
LLM_API_KEY=<compatible-provider key>
OPENAI_API_KEY=<OpenAI key>
FREE_LLM_MODEL=qwen3:8b
PAID_LLM_MODEL=gpt-5.6-sol
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
