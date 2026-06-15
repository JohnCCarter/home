# Home Agent — LLM Wiki

Lätt wiki för AI-agenter som arbetar i detta repo. Målet är snabb, säker orientering utan tung governance.

Detta är ett **personligt Home Agent-repo** — separat från Fibonacci och Genesis-Core-V2.

## Vad wikin är

- En **karta** över projektet, arkitektur och regler
- **Handoff** och beslutshistorik för kontinuitet mellan sessioner
- **Inte** källauktoritet — kod och tester vinner alltid (se [source_authority.md](source_authority.md))

## Sidor

| Sida | Innehåll |
|------|----------|
| [project_context.md](project_context.md) | Mål, scope, framtida klienter |
| [architecture.md](architecture.md) | Flöde, mappar, komponenter |
| [source_authority.md](source_authority.md) | Vad som gäller när docs och kod skiljer sig |
| [tool_contracts.md](tool_contracts.md) | Tool-namn, input/output |
| [auth_and_secrets.md](auth_and_secrets.md) | OAuth, `.env`, tokens |
| [safety_rules.md](safety_rules.md) | Läs/skriv/delete, bekräftelse |
| [development_workflow.md](development_workflow.md) | Enkel arbetsgång |
| [testing.md](testing.md) | Köra tester, mock-provider |
| [handoff.md](handoff.md) | Aktuell status och nästa steg |
| [decision_log.md](decision_log.md) | Arkitekturbeslut |

## Snabbstart för agenter

1. Läs [project_context.md](project_context.md) och [safety_rules.md](safety_rules.md)
2. Gör **små** ändringar; kör tester (se [testing.md](testing.md))
3. Committa aldrig secrets; kontrollera [auth_and_secrets.md](auth_and_secrets.md)
4. Uppdatera [handoff.md](handoff.md) vid större arbete eller sessionsslut

## Relaterat

- [AGENTS.md](../../AGENTS.md) — korta agentregler i repo-roten
- [README.md](../../README.md) — installation och körning
