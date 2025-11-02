---
description: Полный цикл тестирования и исправления с Chrome DevTools - запускает QA агента, исправляет баги, деплоит и повторяет
---

# QA Cycle Command

You are executing the **QA Cycle** command to run automated testing and fixing cycles.

## 🎯 Your Task

Launch the **agent-organizer** to coordinate a full QA automation cycle with the following workflow:

1. **Test** → Run qa-automation agent with Chrome DevTools
2. **Fix** → Delegate bugs to specialist agents (frontend/backend)
3. **Deploy** → Ask confirmation and deploy to production
4. **Retest** → Verify fixes with another test run
5. **Repeat** → Continue until all tests pass or max iterations reached

## 📋 Parameters

### Application URL
```
{{url}}
```
**Default:** Auto-detect from project (http://192.168.0.24:3000 for TextScript)

### Specification Path
```
{{spec_path}}
```
**Default:** Auto-detect latest spec from `specs/*/spec.md`

### Max Iterations
```
{{max_iterations}}
```
**Default:** 3

## 🚀 Execution

**Launch agent-organizer with the QA Cycle workflow:**

```
You are agent-organizer executing the QA Cycle workflow.

Your mission:
Run the qa_cycle_workflow with these parameters:

- URL: {{url}} (default: http://192.168.0.24:3000)
- Spec: {{spec_path}} (default: auto-detect from specs/)
- Max iterations: {{max_iterations}} (default: 3)

Steps:
1. Auto-detect URL and spec path if not provided
2. Execute qa_cycle_workflow algorithm from your prompt
3. Coordinate testing, fixing, and deployment
4. Generate comprehensive summary report

Remember to:
- Ask for deployment confirmation before each deploy
- Provide detailed progress updates
- Handle failures gracefully
- Generate final QA summary report

Begin now.
```

## 📊 Expected Output

You should see:
- **Iteration progress** for each test-fix-deploy cycle
- **Test results** with passed/failed counts
- **Bug categorization** (frontend/backend/design)
- **Deployment confirmations** before each production deploy
- **Final summary** with overall results

## 💡 Usage Examples

### Basic usage (all defaults)
```
/qa-cycle
```

### Custom URL
```
/qa-cycle url=http://localhost:3000
```

### Custom spec and iterations
```
/qa-cycle spec_path=specs/my-feature/spec.md max_iterations=5
```

### Full customization
```
/qa-cycle url=http://192.168.0.24:3000 spec_path=specs/002-web-frontend-docker/spec.md max_iterations=3
```

## ⚙️ Workflow Details

### 1. Testing Phase
- qa-automation reads specification
- Generates test plan from user stories
- Executes E2E tests with Chrome DevTools
- Creates detailed bug reports

### 2. Fixing Phase
- Categorizes bugs by type
- Delegates to specialist agents:
  - `frontend-developer` for UI bugs
  - `python-backend-developer` for API bugs
  - `frontend-developer` for design issues

### 3. Deployment Phase
- **Asks for confirmation** before deploying
- Option to review git diff first
- Deploys via `production-deployment` agent
- Waits for services to stabilize

### 4. Iteration Control
- Continues until tests pass
- Maximum `max_iterations` attempts
- Option to continue if limit reached
- Can stop at any point

## 🎓 Best Practices

1. **Run before major deployments** to catch issues early
2. **Review bug reports** in `test-reports/` directory
3. **Monitor iterations** - if taking too many, check for systemic issues
4. **Use spec-first approach** - ensure spec.md is up-to-date
5. **Check deployment confirmations** carefully before approving

## 🔧 Troubleshooting

### Tests keep failing
- Check if bugs are too complex for automated fixing
- Review test-reports for patterns
- Consider manual intervention

### Deployment fails
- Verify server connectivity (ssh server24)
- Check Docker services status
- Review production-deployment logs

### Agent errors
- Ensure all agents are properly configured
- Check Chrome DevTools MCP is available
- Verify application is accessible at URL

## 📝 Output Files

All QA cycle outputs are saved to:
```
test-reports/
  ├── qa-report-iteration-1-{timestamp}.md
  ├── qa-report-iteration-2-{timestamp}.md
  └── qa-report-iteration-3-{timestamp}.md
```

Reports include:
- Executive summary
- Test results by user story
- Detailed bug reports with screenshots
- Console and network errors
- Recommendations for fixes

---

**Ready to start automated testing and fixing cycles!** 🚀
