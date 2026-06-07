# Implementation Plan: AgentThat Platform

## Overview

This plan implements the AgentThat enterprise AI adoption operating system as a modular FastAPI backend with a Next.js 16 frontend. The implementation follows an incremental approach: foundational data layer and auth first, then core domain services (Solution Architect, Prompt Engine, Agent Studio, Orchestration), followed by supporting services (Marketplace, Adoption, Learning), and finally cross-cutting concerns (Observability, Background Jobs, Collaboration). Each phase wires into the existing project structure and builds on prior phases.

## Tasks

- [ ] 1. Foundation: Database models, tenant isolation, and repository layer
  - [x] 1.1 Create SQLAlchemy database models for Tenant, User, Agent, AgentVersion, AgentStateTransition
    - Create `backend/app/models/db/tenant.py` with Tenant model (id, name, tier, data_region, max_concurrent_jobs, hourly_cost_rate, currency, audit_retention_days)
    - Create `backend/app/models/db/user.py` with User model (id, tenant_id, external_id, email, display_name, role, status, group_memberships, last_login_at)
    - Create `backend/app/models/db/agent.py` with Agent, AgentVersion, AgentStateTransition models per design document
    - Create `backend/app/models/db/__init__.py` exporting all models
    - _Requirements: 15.2, 16.1, 3.2, 3.3, 26.1_

  - [x] 1.2 Create SQLAlchemy database models for Workflow, WorkflowVersion, WorkflowStep, ExecutionRun, StepExecution, ContextEntry
    - Create `backend/app/models/db/workflow.py` with Workflow, WorkflowVersion, WorkflowStep models
    - Create `backend/app/models/db/execution.py` with ExecutionRun, StepExecution, ContextEntry models
    - Include all fields, foreign keys, and constraints per design ER diagram
    - _Requirements: 7.1, 6.1, 6.11, 28.4_

  - [x] 1.3 Create SQLAlchemy database models for Marketplace, Rating, Review, BackgroundJob, AuditLog, MCPServer
    - Create `backend/app/models/db/marketplace.py` with MarketplaceListing, Rating, Review models (include UniqueConstraints)
    - Create `backend/app/models/db/job.py` with BackgroundJob model
    - Create `backend/app/models/db/audit.py` with AuditLog model
    - Create `backend/app/models/db/mcp_server.py` with MCPServer, MCPServerVersion models
    - _Requirements: 9.1, 10.1, 10.3, 17.1, 8.1, 21.1_

  - [x] 1.4 Create SQLAlchemy database models for Course, Enrollment, Certification, LearningPath
    - Create `backend/app/models/db/learning.py` with Course, Enrollment, Certification models
    - Include prerequisite_ids JSONB, assessment_config JSONB, completion tracking fields
    - _Requirements: 13.1, 13.3, 13.4, 14.1, 14.2_

  - [x] 1.5 Create tenant-aware base repository with automatic tenant scoping
    - Create `backend/app/repositories/base.py` with TenantScopedRepository class
    - All queries must inject `WHERE tenant_id = :tenant_id` automatically
    - Provide `get_by_id`, `list_all`, `create`, `update`, `delete` methods that enforce tenant isolation
    - Raise authorization error if tenant_id is missing or mismatched
    - _Requirements: 19.1, 19.2, 16.4_

  - [ ] 1.6 Create database connection, session management, and Alembic migration configuration
    - Create `backend/app/db.py` with async SQLAlchemy engine, session factory, and dependency injection
    - Configure `backend/alembic/env.py` to detect all models
    - Generate initial migration with all tables, indexes, and constraints from design
    - Include composite indexes (tenant+state, tenant+created, tenant+status) and GIN indexes
    - _Requirements: 19.1, 19.3_

  - [ ]* 1.7 Write property test for tenant data isolation (Property 5)
    - **Property 5: Tenant data isolation**
    - Generate multi-tenant data sets and verify that repository queries never return cross-tenant data
    - Use Hypothesis to generate random tenant_id pairs and verify scoping
    - **Validates: Requirements 19.1, 19.2, 28.5, 16.4**

- [ ] 2. Authentication, authorization, and audit infrastructure
  - [x] 2.1 Implement JWT authentication middleware with tenant context extraction
    - Create `backend/app/middleware/auth.py` with JWT validation, tenant_id/user_id/role extraction
    - Support Bearer token format; extract claims for tenant_id, user_id, roles, email
    - Create FastAPI dependency `get_current_user` returning authenticated user context
    - Configure session timeout and token refresh validation
    - _Requirements: 15.1, 15.2, 15.3_

  - [x] 2.2 Implement RBAC permission enforcement middleware
    - Create `backend/app/middleware/rbac.py` with role hierarchy (Admin > Developer > User)
    - Create `require_role(min_role)` decorator/dependency for route protection
    - Implement attribute-based access control (workspace membership, resource ownership/sharing)
    - Deny with 403 and generic message on failure
    - _Requirements: 16.1, 16.2, 16.3, 16.6_

  - [x] 2.3 Implement audit logging service with append-only guarantee
    - Create `backend/app/services/audit.py` with AuditService class
    - Record: timestamp (UTC ISO 8601 ms), user_id, tenant_id, operation, resource_type, resource_id, outcome
    - Enforce append-only (no update/delete before retention expiry)
    - Block mutations if audit system unavailable (fail-closed)
    - Support search/export filtered by time, user, operation, resource (max 10,000 results, CSV/JSON)
    - _Requirements: 17.1, 17.2, 17.5, 17.6, 17.7_

  - [x] 2.4 Implement audit logging API endpoints
    - Create `backend/app/api/v1/audit.py` with GET `/v1/audit` (search), GET `/v1/audit/export` (CSV/JSON)
    - Apply admin-only RBAC
    - Filter by time_range, user_id, operation_type, resource_id
    - _Requirements: 17.7_

  - [ ]* 2.5 Write property tests for RBAC enforcement (Property 14) and audit completeness (Property 19)
    - **Property 14: RBAC permission enforcement**
    - **Property 19: Audit log entry completeness**
    - Generate random role/operation combinations and verify access decisions
    - Generate random CRUD operations and verify audit entries contain all required fields
    - **Validates: Requirements 16.1, 16.2, 16.3, 17.1, 17.2**

- [ ] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Background job processing and real-time streaming
  - [ ] 4.1 Implement Redis-backed job queue with priority ordering and tenant concurrency limits
    - Create `backend/app/services/job_queue.py` with JobQueueService
    - Enqueue jobs with priority (tenant tier + timestamp), return job_id within 2 seconds
    - Enforce per-tenant concurrency limits (1-20 simultaneous jobs)
    - Support job states: queued, processing, completed, failed, cancelled, timed_out
    - Auto-timeout jobs exceeding 30 minutes
    - _Requirements: 8.1, 8.5, 8.6_

  - [ ] 4.2 Implement SSE/WebSocket streaming for job progress updates
    - Create `backend/app/api/v1/jobs.py` with GET `/v1/jobs/{id}`, GET `/v1/jobs/{id}/stream` (SSE), POST `/v1/jobs/{id}/cancel`
    - Emit progress updates every ≤5 seconds (job_id, percentage 0-100, status message ≤200 chars)
    - Store completed results for 7 days minimum
    - Notify on completion/failure via stream and persistent notification
    - _Requirements: 8.2, 8.3, 8.4, 8.7_

  - [ ] 4.3 Implement event-driven job execution worker with phase-based processing
    - Create `backend/app/workers/job_worker.py` with Celery/ARQ worker
    - Process generation jobs in phases (analysis → design → configuration → validation)
    - Each phase emits completion event triggering next phase
    - Stream intermediate results as phases complete
    - Auto-route requests >4000 chars to background queue
    - _Requirements: 8.8, 8.9, 8.10_

  - [ ]* 4.4 Write property test for job priority ordering (Property 18)
    - **Property 18: Background job priority ordering**
    - Generate random job sets with varying tenant tiers and timestamps
    - Verify processing order: higher tier first, then earlier timestamp
    - **Validates: Requirements 8.6**

- [ ] 5. Solution Architect Service
  - [x] 5.1 Implement requirement validation with length and business intent checks
    - Create `backend/app/services/solution_architect.py` with SolutionArchitectService
    - Validate input length (20-8000 chars), reject outside range with error message
    - Detect business intent (minimum 2 domain-relevant terms), prompt refinement if insufficient
    - _Requirements: 1.2, 1.8_

  - [x] 5.2 Implement LLM-powered solution generation with structural completeness
    - Add `generate()` method using Azure OpenAI to produce complete solution architecture
    - Output must include: agents (name, purpose, prompt, tools, handoff), workflow (steps, ordering, assignments, human-approval), integrations, governance (tenant isolation, RBAC, audit, approval triggers), memory config (adapter type, retention, context window per agent), RAG config (knowledge sources, embedding model, chunking, retrieval, thresholds), deployment config (environment, scaling, resource limits, region)
    - Enforce 60-second generation timeout
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 1.6, 1.9, 1.10, 1.11_

  - [x] 5.3 Implement rule-based fallback generator for LLM unavailability
    - Add `fallback_generate()` method producing valid solution meeting same structural requirements
    - Must satisfy same structure: agents, workflow, integrations, governance, memory, RAG, deployment
    - Include `provider: "deterministic"` indicator in response
    - _Requirements: 1.7_

  - [x] 5.4 Create Solution Architect API endpoints
    - Create `backend/app/api/v1/solutions.py` with POST `/v1/solutions/generate`, GET `/v1/solutions`, POST `/v1/solutions/{id}/deploy`, DELETE `/v1/solutions/{id}`
    - Route payloads >4000 chars to background job queue automatically
    - Wire auth, RBAC, audit logging, tenant scoping
    - _Requirements: 1.1, 1.2, 8.8_

  - [ ]* 5.5 Write property tests for solution structural completeness (Property 1) and input validation (Property 2)
    - **Property 1: Solution generation structural completeness**
    - **Property 2: Input length boundary validation**
    - Generate valid requirement strings and verify all structural components present
    - Generate strings at boundary lengths and verify rejection/acceptance
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.9, 1.10, 1.11**

  - [ ]* 5.6 Write property test for fallback structural validity (Property 3)
    - **Property 3: Fallback generation structural validity**
    - Verify fallback output matches same structural requirements as LLM path
    - **Validates: Requirements 1.7, 2.4**

- [ ] 6. Prompt Improvement Engine
  - [x] 6.1 Implement prompt improvement service with LLM and deterministic fallback
    - Create `backend/app/services/prompt_engine.py` with PromptImprovementEngine
    - Accept prompt (3-6000 chars), optional business context (up to 2000 chars)
    - LLM path: return improved prompt + 1-10 categorized improvements within 30 seconds
    - Detect/resolve ambiguity, identify missing requirements, enhance context/instructions/output/constraints/success criteria
    - Fallback (10s LLM timeout): deterministic improvement using predefined rules with fallback indicator
    - Preserve original intent (goals, constraints, subject matter)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ] 6.2 Implement selective improvement acceptance and alternative generation
    - Add accept/reject per improvement; apply only accepted improvements
    - Add alternative generation (up to 3 versions: conciseness, detail, structure focused)
    - _Requirements: 2.7, 2.8_

  - [ ] 6.3 Implement prompt version history
    - Create prompt versioning: store improvements as new versions linked to original
    - Support comparison between any two versions showing additions/removals/modifications
    - _Requirements: 2.9_

  - [x] 6.4 Create Prompt Engine API endpoints
    - Create `backend/app/api/v1/prompts.py` with POST `/v1/prompts/improve`, POST `/v1/prompts/alternatives`, GET `/v1/prompts/{id}/versions`, POST `/v1/prompts/{id}/accept`
    - Wire auth, RBAC, audit, tenant scoping
    - _Requirements: 2.1, 2.6, 2.7, 2.8, 2.9_

- [ ] 7. Agent Generation Studio
  - [x] 7.1 Implement manual agent creation service with validation
    - Create `backend/app/services/agent_studio.py` with AgentStudioService
    - Validate: name (2-120 chars), description (4-1000 chars), category from tenant list
    - Require minimum one prompt block and one tool component for completeness
    - Persist with unique ID, testing status, zero usage, creation timestamp
    - Display available MCP servers and built-in tools filtered by category and tenant permissions
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [ ] 7.2 Implement AI generation mode for agents and workflows
    - Add AI generation accepting natural language (10-2000 chars)
    - Generate agent config: name, tools (from registry), memory adapter, governance defaults, handoff rules
    - Support modes: single agent, multi-agent workflow, optimization of existing
    - Present generated config in visual builder for review before save
    - Display progress indicator during generation; timeout at 60 seconds with error
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

  - [ ] 7.3 Implement optimization mode for existing workflows
    - Add optimization analysis: detect performance bottlenecks (>50% above avg), redundant steps, missing error handling, suboptimal agent configs
    - Return up to 20 recommendations with category, affected step, description, expected impact
    - If zero findings, display confirmation message
    - Apply accepted optimizations as new workflow version, preserve previous version
    - Revert partial changes on failure
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [x] 7.4 Create Agent Studio API endpoints
    - Create `backend/app/api/v1/agents.py` with full CRUD: POST/GET/PUT `/v1/agents`, POST `/v1/agents/generate`, POST `/v1/agents/{id}/optimize`
    - Wire auth, RBAC, audit, tenant scoping, background job routing for large payloads
    - _Requirements: 3.2, 3.3, 4.1, 4.6, 5.1_

  - [ ]* 7.5 Write property test for agent creation initial state invariants (Property 12)
    - **Property 12: Agent creation initial state invariants**
    - Verify: unique ID, lifecycle_state in (draft, testing), usage_count=0, valid timestamp, all required fields
    - **Validates: Requirements 3.3, 9.6**

- [ ] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Agent Lifecycle Management
  - [x] 9.1 Implement agent lifecycle state machine with transition validation
    - Create `backend/app/services/agent_lifecycle.py` with AgentLifecycleManager
    - Valid transitions: Draft→Testing→Staging→Production→Deprecated→Retired, any→Retired
    - Reject invalid transitions with error (current state + allowed targets)
    - Production requires successful sandbox test in last 7 days + Developer/Admin approval
    - Deprecated: configure deprecation message (1-500 chars), optional replacement agent ID
    - Retired: terminate active executions within 60s, remove from workflow assignments, retain for audit
    - Record transition history (timestamp, actor, from_state, to_state)
    - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7_

  - [ ] 9.2 Create agent lifecycle API endpoint
    - Add POST `/v1/agents/{id}/transition` endpoint with target_state, reason
    - GET `/v1/agents/{id}/versions` for version history
    - Wire auth (Developer+ required), RBAC, audit
    - _Requirements: 26.2, 26.3, 26.7_

  - [ ]* 9.3 Write property test for agent lifecycle state machine (Property 4)
    - **Property 4: Agent lifecycle state machine validity**
    - Generate random (current_state, target_state) pairs and verify correct accept/reject
    - **Validates: Requirements 26.1, 26.2, 26.3**

- [ ] 10. Workflow Orchestration Engine
  - [x] 10.1 Implement workflow CRUD with lifecycle commands (run/pause/resume)
    - Create `backend/app/services/orchestrator.py` with WorkflowOrchestrator
    - Create workflow: validate name (3-120), description (8-1000), agents (1-12)
    - State transitions: run (draft|paused→active), pause (active→paused), resume (paused→active)
    - Reject invalid commands with error (current status + allowed transitions)
    - Update lastRun timestamp on each step execution
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_

  - [ ] 10.2 Implement sequential and parallel execution patterns
    - Sequential: each agent completes before next begins
    - Parallel: independent agents execute concurrently
    - Support 2-12 agents, agent teams, agent hierarchies
    - Record every state transition, agent invocation, tool call, decision point in immutable execution log (90 day retention)
    - _Requirements: 6.1, 6.2, 6.3, 6.11_

  - [ ] 10.3 Implement human-in-the-loop with configurable timeout and dynamic routing
    - Human-in-the-loop: pause at designated steps, wait for approval, timeout 1min-7days (default 24h)
    - On timeout: execute configured action (approve, reject, escalate)
    - Dynamic routing: select next agent from routing map based on output value
    - If no route matches + no default: halt and log unmatched output
    - If no route matches + default configured: execute default route
    - _Requirements: 6.4, 6.5, 6.6_

  - [ ] 10.4 Implement escalation, retry with backoff, and failure recovery
    - Escalation: route to higher-authority agent/human when confidence < threshold (default 0.7)
    - Retry: 1-10 attempts (default 3), backoff strategy (fixed/linear/exponential)
    - On retry exhaustion + recovery path: execute recovery, log full context
    - On retry exhaustion + no recovery: halt workflow, mark failed, log full context
    - _Requirements: 6.7, 6.8, 6.9, 6.10_

  - [x] 10.5 Create workflow orchestration API endpoints
    - Create `backend/app/api/v1/workflows.py` with POST/GET `/v1/workflows`, POST `/v1/workflows/{id}/control`, POST `/v1/workflows/{id}/optimize`
    - Create `backend/app/api/v1/executions.py` with GET `/v1/executions`, GET `/v1/executions/{id}`, POST `/v1/executions/{id}/approve`, GET `/v1/executions/{id}/stream`
    - _Requirements: 7.1, 7.3, 6.4_

  - [ ]* 10.6 Write property tests for workflow state transitions (Property 13) and routing correctness (Property 6)
    - **Property 13: Workflow state transition validity**
    - **Property 6: Workflow dynamic routing correctness**
    - Generate random status/command pairs for transition testing
    - Generate random output values and routing maps for routing testing
    - **Validates: Requirements 7.3, 7.4, 7.5, 7.6, 6.5, 6.6**

  - [ ]* 10.7 Write property tests for escalation (Property 7) and retry (Property 8)
    - **Property 7: Escalation threshold decision**
    - **Property 8: Retry with backoff correctness**
    - Generate random confidence scores and thresholds
    - Generate retry configs and verify attempt counts and backoff timing
    - **Validates: Requirements 6.7, 6.8, 6.9, 6.10**

- [ ] 11. Context Management and Planning Engine
  - [ ] 11.1 Implement context manager for multi-agent communication
    - Create `backend/app/services/context_manager.py` with ContextManager
    - Pass agent output as structured context: summary (max 500 tokens), full output reference, metadata (agent_id, step, timestamp, confidence)
    - Enforce configurable max context window (default 8000 tokens, 2000-128000 range)
    - Apply summarization when exceeding limit, preserve key facts/decisions/data
    - Merge parallel outputs: preserve source identity, order by relevance
    - Maintain shared context store per execution (read/write, tagged entries: fact/decision/data/instruction)
    - Deny cross-tenant context access
    - Produce running summary after 10+ agent invocations
    - Record context events in execution trace
    - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6, 28.7_

  - [ ] 11.2 Implement planning engine for complex task decomposition
    - Create `backend/app/services/planning_engine.py` with PlanningEngine
    - Detect complex tasks (>200 chars or >2 objectives)
    - Decompose into 2-20 steps: goal, tools, expected output, dependencies (no circular deps)
    - Present plan for user review/modification before execution
    - Evaluate each step output against criteria (threshold 0.7); trigger re-plan on deviation
    - On step failure after retries: re-plan with alternative approach, present for approval
    - Produce execution summary (time, completed/revised/failed steps, outcome)
    - Store completed plans for 90 days; allow reuse as templates
    - Allow user to pause/modify/add/remove steps during execution
    - _Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7_

  - [ ]* 11.3 Write property tests for context window enforcement (Property 11) and plan structure (Property 24)
    - **Property 11: Context window enforcement**
    - **Property 24: Plan structure invariants**
    - Generate random context sizes and verify summarization triggers at limit
    - Generate complex tasks and verify plan step count (2-20), no circular dependencies
    - **Validates: Requirements 28.2, 27.1**

  - [ ]* 11.4 Write property test for plan deviation detection (Property 25)
    - **Property 25: Plan deviation detection**
    - Generate step outputs with varying similarity scores and verify re-plan triggers
    - **Validates: Requirements 27.3**

- [ ] 12. Multi-Agent Collaboration and Long-Running Workflows
  - [ ] 12.1 Implement agent delegation and collaboration within workflows
    - Extend orchestrator with delegation: pass subtask + context to target agent, wait for result
    - Validate target agent eligibility (permissions, lifecycle state: Testing/Staging/Production)
    - Support collaboration exchanges (max 10 per session, configurable)
    - On max exchanges without convergence: terminate, use last message as output, log warning
    - Distribute intermediate outputs to multiple downstream agents simultaneously
    - Support agent-initiated human approval requests (question 1-500 chars, 2-5 options)
    - Record all delegation, collaboration, and approval events in execution trace
    - _Requirements: 29.1, 29.2, 29.3, 29.4, 29.5, 29.6, 29.7_

  - [ ] 12.2 Implement long-running workflow checkpointing and recovery
    - Persist checkpoint at every step completion and every ≤60s during long steps (when execution >5min)
    - Checkpoint includes: current step, context, variables, pending approvals
    - Auto-resume from checkpoint within 120s of system recovery
    - Re-execute only partially completed step on recovery
    - Support scheduled steps (pause 1min-30days, resume within 60s tolerance)
    - Zero compute while waiting (event-driven triggers)
    - Support 30-day total workflow duration
    - Timeout waiting workflows (default 7 days, 1hr-30days), notify owner, preserve state for 30 days
    - _Requirements: 30.1, 30.2, 30.3, 30.4, 30.5, 30.6, 30.7_

  - [ ]* 12.3 Write property test for collaboration exchange limit (Property 22) and timeout enforcement (Property 23)
    - **Property 22: Collaboration exchange limit enforcement**
    - **Property 23: Long-running workflow timeout enforcement**
    - Generate random exchange sequences and verify limit enforcement
    - Generate workflows with varying wait durations and verify timeout behavior
    - **Validates: Requirements 29.3, 29.4, 30.7**

- [ ] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Agent Runtime and MCP Server Management
  - [ ] 14.1 Implement agent runtime with LangGraph/PydanticAI workers
    - Create `backend/app/services/agent_runtime.py` with AgentRuntime
    - Execute agents with isolated execution contexts (dedicated memory space per invocation)
    - Sandbox tool execution: 30s timeout, 512MB memory, network restricted to policy-permitted destinations
    - Terminate on resource limit violation, return error, preserve agent state
    - Provide memory adapters: short-term (session Redis), long-term (PostgreSQL), semantic (Vector DB)
    - Enforce approved knowledge source policies, reject unauthorized access
    - Record token usage, latency (ms), cost per invocation/tool call (90-day retention)
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5, 20.6_

  - [ ] 14.2 Implement MCP server management service
    - Create `backend/app/services/mcp_manager.py` with MCPServerManager
    - Create MCP server from API/specification/documentation/database schema (within 60s)
    - Validate for MCP protocol compliance, activate within 30s on success
    - On validation failure: retain draft state, display non-compliant elements
    - Authenticate connections with tenant-scoped credentials
    - Version management: retain 10+ recent versions, rollback within 30s, maintain backward compatibility
    - Handle invalid input sources (unreachable API, malformed spec): abort, preserve state, error message
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5, 21.6, 21.7_

  - [ ] 14.3 Create MCP server API endpoints
    - Create `backend/app/api/v1/mcp_servers.py` with POST/GET `/v1/mcp-servers`, POST `/v1/mcp-servers/{id}/activate`, POST `/v1/mcp-servers/{id}/rollback`, GET `/v1/mcp-servers/{id}/versions`
    - Wire auth, RBAC, audit, tenant scoping
    - _Requirements: 21.1, 21.2, 21.6_

- [ ] 15. Marketplace Service
  - [ ] 15.1 Implement marketplace publishing and discovery
    - Create `backend/app/services/marketplace.py` with MarketplaceService
    - Publish: require name (1-100), creator_id, description (1-2000), category, type (agent/workflow/template/mcp_server/integration), initial install_count=0
    - Reject duplicate listing name within tenant
    - Search: filter by category, rating, install count, text search (name + description), max 50/page, ordered by relevance
    - Install: increment count, create independent copy in user tenant workspace within 10s, set testing status
    - On install failure: no workspace modification, display error
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [ ] 15.2 Implement marketplace social features (rating, review, clone, fork)
    - Rating: 1.0-5.0 in 0.5 increments, one per user per item, recalculate average within 5s
    - Replace previous rating on re-submission
    - Review: 1-2000 chars, one per user per item, with timestamp
    - Clone: independent copy (no link to original)
    - Fork: linked copy (record original ID + version), notify on new version
    - Reject self-rating/review (owner cannot rate own items)
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

  - [ ] 15.3 Create marketplace API endpoints
    - Create `backend/app/api/v1/marketplace.py` with GET/POST `/v1/marketplace`, GET `/v1/marketplace/{id}`, POST `/v1/marketplace/{id}/install`, `/clone`, `/fork`, `/rate`, `/review`
    - Wire auth, RBAC, audit, tenant scoping
    - _Requirements: 9.1, 9.3, 10.1, 10.4, 10.5_

  - [ ]* 15.4 Write property tests for rating aggregation (Property 9), search filtering (Property 10), and self-rating prevention (Property 20)
    - **Property 9: Marketplace rating aggregate correctness**
    - **Property 10: Marketplace search filter compliance**
    - **Property 20: Self-rating prevention**
    - Generate random rating sequences and verify aggregate equals mean of latest per user
    - Generate listings + filters and verify all results satisfy all active filters
    - Generate owner/non-owner attempts and verify rejection for owners
    - **Validates: Requirements 10.1, 10.2, 9.3, 10.6**

- [ ] 16. Adoption Platform and Analytics
  - [ ] 16.1 Implement adoption metrics tracking and calculation
    - Create `backend/app/services/adoption.py` with AdoptionPlatformService
    - Track per execution: cost (USD 4 decimals), latency per agent/tool/step (ms), token usage (in/out), error count
    - Calculate: adoption rate (active/total×100), efficiency (auto_time/manual_time×100), time saved (hours), cost reduction, ROI ((reduction-cost)/cost×100)
    - Compute escalation/approval/policy-block rates (% to 2 decimals, rolling 7d and 30d)
    - Display per department: active users, total executions, adoption %
    - Update aggregates within 5 minutes of execution completion
    - Scope analytics to authenticated team lead's team
    - Exclude partially recorded executions with indicator
    - _Requirements: 11.1, 11.2, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

  - [ ] 16.2 Implement report generation and export
    - Generate reports within 30 seconds aggregated by department, team, time period (weekly/monthly/quarterly), asset type
    - Provide time-series data (monthly granularity, 12+ months retention)
    - Export formats: dashboard view, PDF, presentation outline (titled sections, summary metrics, trend charts, key findings)
    - Insufficient sample indicator for groups <5 executions
    - _Requirements: 11.3, 11.4, 11.5, 11.6_

  - [ ] 16.3 Create analytics API endpoints
    - Create `backend/app/api/v1/analytics.py` with GET `/v1/analytics`, GET `/v1/analytics/reports`, POST `/v1/analytics/export`
    - Wire auth, RBAC (team-scoped for leads, org-scoped for executives), tenant scoping
    - _Requirements: 11.3, 12.5_

  - [ ]* 16.4 Write property test for adoption metric calculations (Property 21)
    - **Property 21: Adoption metric calculation correctness**
    - Generate random execution data sets and verify formula correctness for adoption rate, efficiency, time saved, ROI
    - **Validates: Requirements 11.1, 11.2**

- [ ] 17. Learning Platform
  - [ ] 17.1 Implement course management and enrollment with prerequisites
    - Create `backend/app/services/learning.py` with LearningPlatformService
    - Provide courses for: AI fundamentals, prompt engineering, agent building, multi-agent design, advanced optimization
    - Organize into role-based learning paths (Employee Builder, Team Lead, Platform Admin) with sequential progression
    - Track enrollment: lesson completion % (lessons_done/total×100), time spent (minutes)
    - Course definition: title (≤120), description (≤500), duration (hours), lesson count (1-50), status (available/in_progress/completed)
    - Enforce prerequisites: reject enrollment if prerequisites incomplete, indicate which remain
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.6_

  - [ ] 17.2 Implement assessments and certifications
    - 10+ question assessment per course, 70% passing score
    - Certification levels: Beginner, Intermediate, Advanced (1-10 required courses each)
    - Award certification on passing all required assessments (timestamp, display on profile within 5s)
    - Track progress: completed/required courses as ratio
    - On failure: display score, topics to review, allow reattempt after 24 hours (unlimited total)
    - Team lead dashboard: member certification status, earned certifications, progress
    - Award certification when all courses in learning path completed
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 13.5_

  - [ ] 17.3 Create learning platform API endpoints
    - Create `backend/app/api/v1/learning.py` with GET `/v1/learning/courses`, POST `/v1/learning/enroll`, POST `/v1/learning/assess`, GET `/v1/learning/certifications`, GET `/v1/learning/team-progress`
    - Wire auth, RBAC, tenant scoping
    - _Requirements: 13.1, 14.1, 14.6_

  - [ ]* 17.4 Write property tests for prerequisite enforcement (Property 17) and certification threshold (Property 16)
    - **Property 17: Learning path prerequisite enforcement**
    - **Property 16: Certification award threshold**
    - Generate random prerequisite completion states and verify enrollment decisions
    - Generate random assessment scores and verify certification award/denial
    - **Validates: Requirements 13.2, 13.6, 14.1, 14.2, 14.3**

- [ ] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Observability and Tracing
  - [ ] 19.1 Implement OpenTelemetry instrumentation for all services
    - Create `backend/app/services/observability.py` with tracing setup
    - Instrument agent executions, tool calls, workflow steps with span hierarchy
    - Include metadata: tenant_id, agent_id, workflow_id, user_id, model_name, token_count per span
    - Forward to configured backends (LangFuse) within 30s of span completion
    - Buffer locally for 10min if backend unreachable, retry with exponential backoff, discard >10min data
    - _Requirements: 22.1, 22.2, 22.3_

  - [ ] 19.2 Implement alerting and trace visualization endpoints
    - Emit error alerts to notification channel within 60s
    - Emit latency alerts when step >30s or workflow >300s (admin-configurable thresholds)
    - Provide trace visualization: execution flow, span hierarchy, timing, token usage, cost per step (query <3s for 90-day traces)
    - Partition data by tenant and time (daily), 90-day retention, p95 query <3s
    - _Requirements: 22.4, 22.5, 22.6, 22.7_

- [ ] 20. Data Protection and Encryption
  - [ ] 20.1 Implement encryption, secrets management, and PII protection
    - Configure AES-256 encryption at rest (database, object storage, backups) with key rotation ≤90 days
    - Enforce TLS 1.2+ for all communications
    - Integrate managed vault (Azure Key Vault) for secrets; never persist in source control/env vars/images
    - Implement PII redaction in logs/traces (names, emails, IPs, tokens) unless tenant audit config requires
    - Support per-tenant data residency controls
    - Block writes if key management unavailable (return error, never write unencrypted)
    - Audit log secret access (accessor, timestamp, secret_id)
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_

- [ ] 21. Frontend: Dashboard and Navigation
  - [x] 21.1 Implement platform dashboard with aggregate stats, activity feed, and quick actions
    - Update `frontend/src/app/page.tsx` to fetch from `/v1/platform/overview`
    - Display stats: total agents, active workflows, team members, avg efficiency (30-day mean success rate)
    - Activity feed: up to 20 events (agent creation, workflow deployment, prompt improvement, marketplace install) reverse chronological
    - Quick actions: create agent, create workflow, browse marketplace
    - Active agents list: up to 10, sorted by usage desc, showing name/description/category/usage/status
    - Handle backend unavailable: show cached data with stale indicator
    - Empty state: direct to quick actions for first-time users
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6_

  - [ ] 21.2 Implement Zustand stores for agents, workflows, jobs, and notifications
    - Create `frontend/src/stores/agent-store.ts` with agent CRUD state
    - Create `frontend/src/stores/workflow-store.ts` with workflow state and lifecycle commands
    - Create `frontend/src/stores/job-store.ts` with background job tracking and SSE connection
    - Create `frontend/src/stores/notification-store.ts` with persistent notification management
    - _Requirements: 23.1, 8.2, 8.3_

- [ ] 22. Frontend: Agent Builder and Generation
  - [x] 22.1 Implement agent builder canvas (visual drag-and-drop)
    - Update `frontend/src/app/builder/page.tsx` with visual canvas for agent components
    - Support drag-and-drop: tools, memory adapters, prompt blocks, handoff connections (max 50 components)
    - Validate completeness (min 1 prompt + 1 tool with connections) before save
    - Show validation errors indicating missing components/connections
    - Display available MCP servers and built-in tools filtered by category
    - _Requirements: 3.1, 3.4, 3.5, 3.6_

  - [x] 22.2 Implement AI generation mode UI with progress indicator
    - Add natural language input (10-2000 chars) for AI generation
    - Display progress indicator during generation
    - Present generated config in visual builder for review/modification before save
    - Support single agent, multi-agent, and optimization modes
    - Handle timeout/errors with user guidance
    - _Requirements: 4.1, 4.3, 4.5, 4.6, 4.7_

  - [ ] 22.3 Implement optimization mode UI
    - Add optimization analysis trigger for existing workflows
    - Display findings list (up to 20) with category, affected step, description, expected impact
    - Allow accept/reject per recommendation
    - Show version history access for applied optimizations
    - Display "no findings" confirmation when applicable
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 23. Frontend: Workflow Editor and Execution Viewer
  - [x] 23.1 Implement workflow creation, control, and monitoring UI
    - Update `frontend/src/app/workflows/page.tsx` with workflow list + create dialog
    - Workflow creation form: name (3-120), description (8-1000), agent count (1-12) with validation
    - Control buttons: Run/Pause/Resume with appropriate state-based visibility
    - Display current status, executing step/total, lastRun timestamp
    - Show invalid command errors with current status and allowed transitions
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.8_

  - [ ] 23.2 Implement execution trace viewer with real-time streaming
    - Create execution trace component showing: execution flow, span hierarchy, timing, token usage, cost per step
    - SSE connection for real-time execution progress
    - Human approval interface: display question, response options, submit approval/denial
    - Show step status indicators (running/completed/failed/waiting)
    - _Requirements: 6.4, 6.11, 22.6, 8.2_

- [ ] 24. Frontend: Marketplace, Analytics, and Learning
  - [x] 24.1 Implement marketplace browse, search, and install UI
    - Update `frontend/src/app/marketplace/page.tsx` with search, filters (category, rating, type), results (max 50/page)
    - Install action with confirmation and success message
    - Rating widget (0.5 increments, 1.0-5.0)
    - Review submission (1-2000 chars)
    - Clone and fork actions
    - Prevent self-rating/review for item owners
    - _Requirements: 9.2, 9.3, 9.4, 10.1, 10.3, 10.4, 10.5, 10.6_

  - [x] 24.2 Implement analytics dashboard and report views
    - Update `frontend/src/app/analytics/page.tsx` with ROI metrics, time-series charts, department breakdown
    - Filter by time period (weekly/monthly/quarterly), department, team, asset type
    - Export actions (PDF, presentation outline)
    - Insufficient sample indicator for groups <5 executions
    - _Requirements: 11.1, 11.3, 11.5, 11.6_

  - [x] 24.3 Implement learning platform UI with courses, paths, and certifications
    - Update `frontend/src/app/learning/page.tsx` with course catalog, enrollment, progress tracking
    - Display learning paths by role with prerequisite indicators
    - Assessment interface with score display and reattempt scheduling
    - Certification display on user profile
    - Team lead dashboard view for team progress
    - _Requirements: 13.1, 13.2, 13.3, 14.3, 14.4, 14.6_

- [ ] 25. Frontend: Settings, Team Collaboration, and Profile
  - [x] 25.1 Implement settings page with profile, notifications, and team management
    - Update `frontend/src/app/settings/page.tsx` with tabbed interface
    - Profile: full name (1-100), email (valid format), role display with validation errors
    - Notifications: individual toggles (agent deployments, workflow runs, team invitations, weekly reports)
    - Integration status display (connected/disconnected per service)
    - Preserve unsaved input on save failure
    - _Requirements: 25.1, 25.2, 25.3, 25.5, 25.6_

  - [ ] 25.2 Implement team collaboration features
    - Team member management: add (email, name 1-100, role), role assignment, status tracking
    - Reject duplicate email additions
    - Admin permission enforcement (can't modify higher-role members)
    - Version history for agents/workflows (up to 50 versions, auto-increment)
    - Comments on agents/workflows (1-2000 chars, name + timestamp display)
    - Conflict detection on concurrent saves: reject, show newer version for review
    - Invitation acceptance flow (invited → active status)
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7, 24.8, 25.4_

  - [ ]* 25.3 Write property test for version auto-increment and conflict detection (Property 15)
    - **Property 15: Version auto-increment and conflict detection**
    - Generate random save sequences and verify monotonic version numbers
    - Generate concurrent save attempts and verify conflict detection
    - **Validates: Requirements 24.5, 24.7**

- [ ] 26. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 27. Multi-Tenancy, Scalability, and Infrastructure
  - [ ] 27.1 Implement horizontal scaling configuration and health checks
    - Configure Kubernetes deployment manifests for API, workers, runtime (2-50 pods each)
    - Implement health/readiness endpoints with 5-second response guarantee
    - Configure rate limiting per tenant
    - _Requirements: 19.3, 19.5_

  - [ ] 27.2 Implement multi-region deployment with replication and failover
    - Configure PostgreSQL async replication (RPO <5s)
    - Configure Redis replication
    - Implement failover with RTO ≤60s
    - Configure rolling/blue-green deployments for zero-downtime (≤0.1% error during transition)
    - _Requirements: 19.4, 19.6_

  - [ ] 27.3 Create deployment configurations for cloud providers
    - Create infrastructure-as-code for Azure (primary), AWS, and GCP
    - Support customer-managed cloud and on-premises deployment
    - Include: load balancer, K8s cluster, PostgreSQL, Redis, Vector DB, Object Storage, Key Vault
    - _Requirements: 19.7_

- [ ] 28. Enterprise SSO Integration
  - [ ] 28.1 Implement SSO authentication with multiple identity providers
    - Create `backend/app/services/identity.py` with IdentityService
    - Support SAML 2.0, OAuth 2.0, OpenID Connect, Microsoft Entra ID
    - Create/update local user from IdP attributes (subject, email, display_name, groups)
    - Configurable session timeout (5min-24hr), token refresh (1-60min)
    - Support MFA when tenant-enabled
    - Log auth failures (source IP, IdP, reason) with generic client error (don't reveal account existence)
    - Deny auth if IdP unreachable within 30s
    - Deny account creation on email conflict, log for admin review
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

- [ ] 29. Final integration and wiring
  - [ ] 29.1 Wire all API routes into FastAPI application with middleware stack
    - Register all v1 routers in `backend/app/main.py`
    - Apply middleware order: CORS → Auth → Tenant → RBAC → Audit → Rate Limit
    - Configure error response format (code, message, details, request_id, timestamp)
    - Implement circuit breaker for LLM calls (5 failures in 60s → 30s open)
    - _Requirements: 15.1, 16.1, 17.1, 19.1_

  - [ ] 29.2 Wire frontend API client with React Query, SSE hooks, and error handling
    - Create `frontend/src/lib/api-client.ts` with typed API methods for all endpoints
    - Create `frontend/src/hooks/use-sse.ts` for job progress and execution streaming
    - Implement React Query cache invalidation patterns across stores
    - Add global error handling with toast notifications
    - Implement graceful degradation: cache last-known-good data, show stale indicator
    - _Requirements: 23.5, 8.2, 8.3_

  - [ ] 29.3 Configure CI/CD pipeline with test automation
    - Update `.github/workflows/ci.yml` with: lint, type-check, unit tests, property tests, integration tests
    - Add Docker Compose for integration test environment (PostgreSQL, Redis, mock LLM)
    - Configure Playwright for critical E2E journeys
    - _Requirements: 19.6_

- [ ] 30. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Backend uses Python (FastAPI, SQLAlchemy, Hypothesis for property tests, pytest)
- Frontend uses TypeScript (Next.js 16, React 19, Zustand, ShadCN UI, Tailwind CSS)
- The existing codebase already has a working FastAPI app and Next.js frontend to build upon

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4"] },
    { "id": 1, "tasks": ["1.5", "1.6"] },
    { "id": 2, "tasks": ["1.7", "2.1", "2.2"] },
    { "id": 3, "tasks": ["2.3", "2.4"] },
    { "id": 4, "tasks": ["2.5", "4.1"] },
    { "id": 5, "tasks": ["4.2", "4.3"] },
    { "id": 6, "tasks": ["4.4", "5.1", "6.1"] },
    { "id": 7, "tasks": ["5.2", "5.3", "6.2", "6.3"] },
    { "id": 8, "tasks": ["5.4", "5.5", "5.6", "6.4", "7.1"] },
    { "id": 9, "tasks": ["7.2", "7.3", "7.4"] },
    { "id": 10, "tasks": ["7.5", "9.1"] },
    { "id": 11, "tasks": ["9.2", "9.3", "10.1"] },
    { "id": 12, "tasks": ["10.2", "10.3", "10.4"] },
    { "id": 13, "tasks": ["10.5", "10.6", "10.7"] },
    { "id": 14, "tasks": ["11.1", "11.2"] },
    { "id": 15, "tasks": ["11.3", "11.4", "12.1"] },
    { "id": 16, "tasks": ["12.2", "12.3"] },
    { "id": 17, "tasks": ["14.1", "14.2"] },
    { "id": 18, "tasks": ["14.3", "15.1"] },
    { "id": 19, "tasks": ["15.2", "15.3"] },
    { "id": 20, "tasks": ["15.4", "16.1"] },
    { "id": 21, "tasks": ["16.2", "16.3", "16.4"] },
    { "id": 22, "tasks": ["17.1", "17.2"] },
    { "id": 23, "tasks": ["17.3", "17.4", "19.1"] },
    { "id": 24, "tasks": ["19.2", "20.1"] },
    { "id": 25, "tasks": ["21.1", "21.2"] },
    { "id": 26, "tasks": ["22.1", "22.2", "22.3"] },
    { "id": 27, "tasks": ["23.1", "23.2"] },
    { "id": 28, "tasks": ["24.1", "24.2", "24.3"] },
    { "id": 29, "tasks": ["25.1", "25.2"] },
    { "id": 30, "tasks": ["25.3", "27.1", "27.2"] },
    { "id": 31, "tasks": ["27.3", "28.1"] },
    { "id": 32, "tasks": ["29.1", "29.2"] },
    { "id": 33, "tasks": ["29.3"] }
  ]
}
```
