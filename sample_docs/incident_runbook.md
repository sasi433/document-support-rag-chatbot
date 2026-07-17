# Northstar Support Systems - Incident Response Runbook

> This runbook describes fictional internal procedures for demonstration purposes.

## Purpose

This runbook defines how Northstar responds to service incidents. The goals are to restore service safely, communicate clearly, and record what was learned.

## Severity levels

| Severity | Definition | Example |
| --- | --- | --- |
| SEV1 | Complete outage, confirmed data loss, or active security incident | All customers cannot sign in |
| SEV2 | Major degradation with no reasonable workaround | Document uploads fail for many customers |
| SEV3 | Limited impact or a workaround is available | One optional integration is delayed |
| SEV4 | General request or cosmetic issue | Incorrect help text |

The incident commander may change the severity when impact becomes clearer.

## Alert acknowledgement and escalation

The primary on-call engineer must acknowledge a SEV1 alert within five minutes and a SEV2 alert within 15 minutes.

If a SEV1 alert is not acknowledged within five minutes, page the secondary on-call engineer. If nobody acknowledges it within another five minutes, escalate to the engineering manager on duty. Do not rely only on chat messages for SEV1 escalation.

On-call schedules and contact details are stored in the approved incident-management system, not in this repository.

## Incident roles

- **Incident commander:** coordinates the response and makes priority decisions.
- **Operations lead:** investigates and performs recovery work.
- **Communications lead:** posts internal and customer-facing updates.
- **Scribe:** records timestamps, decisions, and actions.

One person should not hold more than two roles during a SEV1 incident when additional responders are available.

## Response process

1. Acknowledge the alert and confirm the customer impact.
2. Assign an incident commander and open an incident channel.
3. Record a timeline and preserve relevant logs.
4. Choose the safest mitigation, such as disabling a feature or rolling back a release.
5. Verify recovery using health checks and a customer-facing workflow.
6. Continue monitoring before resolving the incident.

Post status updates at least every 30 minutes for SEV1 and every 60 minutes for SEV2, even when there is no major change.

## After the incident

A SEV1 or SEV2 postmortem must be completed within five business days. It should describe impact, timeline, root cause, detection gaps, corrective actions, owners, and due dates. Postmortems are blameless and focus on improving systems and processes.
