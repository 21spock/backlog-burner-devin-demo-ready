# Demo-ready GitHub issue set

Use these six issues in the take-home narrative. They are intentionally split into three buckets.

## Safe for Devin

### #201 Disable live Devin launch when `DEVIN_API_KEY` is missing
- Type: bounded UI bug
- Why it is safe: localized, reproducible, and easy to validate

### #202 Add triage filter chips so engineers can isolate safe-autonomous issues
- Type: bounded UX enhancement
- Why it is safe: clear acceptance criteria and limited scope

## Needs clarification

### #203 Improve issue import reliability
- Type: vague quality concern
- Why it needs clarification: not enough detail about failure mode, duplication rules, or expected behavior

### #204 Make progress notifications more useful for the engineering team
- Type: product-definition gap
- Why it needs clarification: unclear update channel, message format, and success criteria

## Senior review

### #205 Add role-based approval controls before allowing live issue launches
- Type: security / permissions / compliance
- Why it stays with humans: touches auth and audit requirements

### #206 Support multi-repo and multi-tenant backlog routing for enterprise roll-out
- Type: architecture / platform roadmap
- Why it stays with humans: broad systems design and enterprise tenancy concerns

## Demo flow

1. Import the six demo-ready issues
2. Run triage
3. Show that only #201 and #202 are approved for Devin
4. Launch one or both green issues
5. Sync runs and show status updates / PR / blocker state
