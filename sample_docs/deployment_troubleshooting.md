# Northstar Connector - Deployment Troubleshooting

> The Northstar Connector and the procedures below are fictional and intended for demonstration.

## First checks

When a deployment fails, avoid making several unrelated changes at once. Record the release version and failure time, then check the following in order:

1. Confirm that the container or pod started.
2. Review application and platform logs for the first meaningful error.
3. Verify required environment variables and mounted configuration.
4. Call the `/health` endpoint from inside the deployment network.
5. Compare the failing release with the last working configuration.
6. Roll back if customers are affected and a safe fix is not immediately available.

Secrets must not be copied into tickets, chat messages, or source control.

## Docker troubleshooting

Use `docker compose ps` to check container state and `docker compose logs --tail 200` to review recent output. A container that repeatedly exits commonly indicates invalid configuration, a missing environment variable, or an unavailable dependency.

If the image was recently changed, confirm that the expected tag was pulled. Rebuild only after recording the original error. The Connector is healthy when its `/health` endpoint returns HTTP 200 with `{"status":"ok"}`.

## Kubernetes troubleshooting

Use `kubectl get pods` to identify pending, restarting, or unavailable pods. Then use `kubectl describe pod` to inspect scheduling and probe events, and `kubectl logs` to read application output.

Common causes include:

- `ImagePullBackOff`: incorrect image name, tag, or registry credentials;
- `CrashLoopBackOff`: startup failure or invalid configuration;
- `Pending`: insufficient cluster resources or an unsatisfied scheduling rule;
- readiness probe failure: the process started but is not ready to receive traffic.

Check that ConfigMap keys and Secret references match the deployment manifest. Display only key names during troubleshooting; do not print secret values.

## Rollback procedure

If a new Kubernetes release causes customer impact, pause further changes and run `kubectl rollout undo deployment/<deployment-name>`. Monitor the rollout until the previous ReplicaSet is available, then verify `/health` and one customer-facing workflow.

For Docker Compose, restore the last known working image tag and configuration, then run `docker compose up -d`. Confirm that containers remain stable before resolving the incident.

Document the failed version, observed error, rollback time, and follow-up owner after service is restored.
