# Demo Questions

These questions validate the fictional Northstar Support Systems documents. Each expected answer must be stated directly in the named source document.

| Question | Expected source | Expected answer |
| --- | --- | --- |
| What is the refund policy? | `company_faq.md` | The first subscription payment can be refunded when requested within 14 calendar days; renewals, usage charges, and completed services are normally non-refundable. |
| When is standard customer support available? | `company_faq.md` | Monday through Friday, 08:00-18:00 CET, excluding Swedish public holidays. |
| How many days per week may Sweden-based employees work remotely? | `hr_policy.md` | Up to three days per week with manager approval. |
| What is the ergonomic equipment allowance? | `hr_policy.md` | Up to SEK 3,000 every three years for approved accessories, with receipts and manager approval. |
| How do I factory-reset a Beacon NSB-100? | `product_manual.md` | Hold the recessed Reset button for 10 seconds, release it when the LED flashes amber, wait for restart, and register the device again. |
| What should I do if the Beacon LED remains solid red? | `product_manual.md` | Disconnect power for 30 seconds, reconnect it, and contact support with the serial number if the LED remains red. |
| What happens if nobody acknowledges a SEV1 alert? | `incident_runbook.md` | Page the secondary after five minutes, then escalate to the engineering manager after another five minutes. |
| When is a SEV1 or SEV2 postmortem due? | `incident_runbook.md` | Within five business days. |
| Who should I contact about a billing problem? | `billing_faq.md` | Email billing@northstar.example with the account name, invoice number, and issue description. |
| What happens after a subscription payment fails? | `billing_faq.md` | Northstar retries after three and seven days; the subscription may be suspended after 10 days if payment still fails. |
| What should I check first when a deployment fails? | `deployment_troubleshooting.md` | Check process state, the first meaningful log error, configuration, `/health`, and differences from the last working release. |
| How do I roll back a failed Kubernetes deployment? | `deployment_troubleshooting.md` | Run `kubectl rollout undo deployment/<deployment-name>`, monitor the rollout, then verify `/health` and a customer workflow. |

## Manual validation checklist

- Confirm every expected source file exists under `sample_docs/`.
- Confirm each expected answer is explicitly present in its source.
- Confirm names, schedules, time limits, and contact addresses are consistent.
- Confirm all people, products, organizations, and contact addresses are fictional.
