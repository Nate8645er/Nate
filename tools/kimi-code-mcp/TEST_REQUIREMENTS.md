# Test Requirements for Context Caching Feature (Phase 1)

> **Target Version**: 0.3.0  
> **Feature**: Session Cache Manager  
> **Author**: AI Assistant  
> **Reviewers**: [To be assigned]

---

## 1. Overview

This document defines the test requirements for the Phase 1 Context Caching implementation. The cache manager aims to reduce latency and cost by reusing Kimi sessions for repeated queries to the same codebase.

### Key Features Under Test

| ID | Feature | Priority |
|----|---------|----------|
| F1 | Session creation and caching | P0 |
| F2 | Cache hit detection and reuse | P0 |
| F3 | Cache expiration (time-based) | P0 |
| F4 | Codebase change detection | P1 |
| F5 | LRU eviction policy | P1 |
| F6 | Cache status monitoring | P2 |
| F7 | Manual cache invalidation | P2 |
| F8 | Error handling and recovery | P0 |

---

## 2. Functional Requirements

### 2.1 Session Creation and Caching (F1)

#### TC-F1-001: Initial Cache Creation
**Objective**: Verify that the first call to `kimi_analyze` creates a new cache entry

**Preconditions**:
- Kimi CLI is installed and authenticated
- Target directory is a valid codebase
- No existing cache for the target directory

**Steps**:
1. Call `kimi_analyze` with `work_dir=/path/to/project`, `use_cache=true`
2. Wait for completion
3. Check response for cache miss indicator

**Expected Results**:
- Response contains `[Cache MISS: Created new session ...]`
- Session ID is returned in the response
- `kimi_cache_status` shows 1 entry with hitCount=0

#### TC-F1-002: Session ID Persistence
**Objective**: Verify that created sessions can be reused

**Steps**:
1. Execute TC-F1-001
2. Note the session ID from response
3. Call `kimi_resume` with the same session ID

**Expected Results**:
- `kimi_resume` successfully continues the session
- Context from previous analysis is retained

---

### 2.2 Cache Hit Detection and Reuse (F2)

#### TC-F2-001: Cache Hit on Second Query
**Objective**: Verify that subsequent queries hit the cache

**Preconditions**:
- TC-F1-001 has been executed and cache is active

**Steps**:
1. Call `kimi_analyze` with same `work_dir`, different prompt
2. Wait for completion

**Expected Results**:
- Response contains `[Cache HIT: Reused session ...]`
- Response time is significantly faster than TC-F1-001 (< 50%)
- `kimi_cache_status` shows hitCount=1

#### TC-F2-002: Explicit Session ID Bypasses Cache
**Objective**: Verify that providing explicit session_id skips cache lookup

**Preconditions**:
- TC-F1-001 has been executed

**Steps**:
1. Call `kimi_analyze` with `work_dir` and explicit `session_id`

**Expected Results**:
- No cache indicator in response
- Uses the provided session_id directly

#### TC-F2-003: Disable Cache with use_cache=false
**Objective**: Verify cache can be disabled per-request

**Steps**:
1. Call `kimi_analyze` with `work_dir`, `use_cache=false`

**Expected Results**:
- No cache indicator in response
- New session is created (not from cache)
- Existing cache entry is unaffected

---

### 2.3 Cache Expiration (F3)

#### TC-F3-001: Cache Expires After Max Age
**Objective**: Verify cache expires after configured TTL

**Preconditions**:
- Cache maxAgeMs is set to a short duration for testing (e.g., 5000ms)
- TC-F1-001 has been executed

**Steps**:
1. Wait for maxAgeMs + 1000ms
2. Call `kimi_analyze` with same `work_dir`

**Expected Results**:
- Response contains `[Cache MISS: Created new session ...]`
- Old session is expired, new one created

#### TC-F3-002: Cache Access Resets Expiration
**Objective**: Verify cache TTL is refreshed on access

**Steps**:
1. Execute TC-F1-001
2. Wait for 50% of maxAgeMs
3. Call `kimi_analyze` (cache hit)
4. Wait for 60% of maxAgeMs (total > original TTL)
5. Call `kimi_analyze` again

**Expected Results**:
- Step 3: Cache hit
- Step 5: Cache hit (not expired because TTL was refreshed)

---

### 2.4 Codebase Change Detection (F4)

#### TC-F4-001: Git Commit Hash Detection
**Objective**: Verify cache invalidates on git commit change

**Preconditions**:
- Target directory is a git repository
- TC-F1-001 has been executed

**Steps**:
1. Create a new git commit in the target directory
2. Call `kimi_analyze` with same `work_dir`

**Expected Results**:
- Response contains `[Cache MISS: Created new session ...]`
- Old cache is invalidated due to code change

#### TC-F4-002: Non-Git Directory Fallback
**Objective**: Verify cache works in non-git directories

**Preconditions**:
- Target directory is NOT a git repository
- Has package.json or similar config files

**Steps**:
1. Call `kimi_analyze` with `work_dir`
2. Modify package.json
3. Call `kimi_analyze` again

**Expected Results**:
- Step 1: Cache miss (new cache created)
- Step 3: Cache miss (detected file change via mtime)

---

### 2.5 LRU Eviction Policy (F5)

#### TC-F5-001: Max Size Enforcement
**Objective**: Verify oldest caches are evicted when max size reached

**Preconditions**:
- maxSize is set to 3 for testing

**Steps**:
1. Call `kimi_analyze` with work_dir=/project1
2. Call `kimi_analyze` with work_dir=/project2
3. Call `kimi_analyze` with work_dir=/project3
4. Call `kimi_cache_status`, note 3 entries
5. Call `kimi_analyze` with work_dir=/project4
6. Call `kimi_cache_status`

**Expected Results**:
- Step 4: 3 cache entries present
- Step 6: 3 cache entries present (not 4)
- Oldest entry (/project1) was evicted
- `kimi_cache_status` shows totalEvictions=1

#### TC-F5-002: Access Updates LRU Order
**Objective**: Verify accessing a cache entry updates its LRU position

**Steps**:
1. Create caches for project1, project2, project3 (maxSize=3)
2. Access project1 (should be LRU now)
3. Create cache for project4

**Expected Results**:
- project2 is evicted (least recently used)
- project1 is retained (accessed in step 2)

---

### 2.6 Cache Status Monitoring (F6)

#### TC-F6-001: Basic Statistics
**Objective**: Verify cache statistics are accurate

**Steps**:
1. Call `kimi_cache_status`
2. Execute TC-F1-001, TC-F2-001
3. Call `kimi_cache_status`

**Expected Results**:
- Step 1: All zeros, empty statistics
- Step 3: 
  - totalCachedSessions: 1
  - totalCacheHits: 1
  - totalCacheMisses: 1
  - cacheHitRate: "50.0%"

#### TC-F6-002: Detailed Entry Information
**Objective**: Verify detailed view shows cache entries

**Steps**:
1. Execute TC-F1-001
2. Call `kimi_cache_status` with `detail=true`

**Expected Results**:
- Response includes `entries` array
- Entry shows workDir, sessionId (truncated), hitCount, lastUsed

---

### 2.7 Manual Cache Invalidation (F7)

#### TC-F7-001: Invalidate Specific Directory
**Objective**: Verify single cache entry can be invalidated

**Preconditions**:
- Caches exist for project1 and project2

**Steps**:
1. Call `kimi_cache_invalidate` with `work_dir=/project1`
2. Call `kimi_cache_status`

**Expected Results**:
- Step 1: "Cache invalidated for: /project1"
- Step 2: Only project2 cache remains

#### TC-F7-002: Invalidate All Caches
**Objective**: Verify all caches can be cleared

**Preconditions**:
- Multiple caches exist

**Steps**:
1. Call `kimi_cache_invalidate` without work_dir parameter
2. Call `kimi_cache_status`

**Expected Results**:
- Step 1: "All N cache entries invalidated."
- Step 2: totalCachedSessions: 0

#### TC-F7-003: Invalidate Non-Existent Cache
**Objective**: Verify graceful handling of invalidation miss

**Steps**:
1. Call `kimi_cache_invalidate` with `work_dir=/nonexistent`

**Expected Results**:
- Response: "No cache found for: /nonexistent"
- No error thrown

---

### 2.8 Error Handling and Recovery (F8)

#### TC-F8-001: Cache Warming Timeout
**Objective**: Verify graceful handling of cache warmup timeout

**Preconditions**:
- Cache warmup timeout is set very short (e.g., 1ms) for testing

**Steps**:
1. Clear all caches
2. Call `kimi_analyze` with `work_dir`

**Expected Results**:
- Request continues without cache
- Response includes `[Cache warning: Cache warmup timed out...]`
- Analysis completes successfully

#### TC-F8-002: Invalid Cached Session Recovery
**Objective**: Verify recovery when cached session becomes invalid

**Steps**:
1. Execute TC-F1-001 to create cache
2. Manually invalidate the session (via Kimi CLI or wait for expiration)
3. Call `kimi_analyze` with same `work_dir`

**Expected Results**:
- First attempt fails with session error
- Cache is automatically invalidated
- Error message suggests retry
- Subsequent call succeeds with new cache

#### TC-F8-003: Kimi CLI Not Installed
**Objective**: Verify graceful error when Kimi is not available

**Preconditions**:
- Kimi CLI is not installed or not in PATH

**Steps**:
1. Call `kimi_analyze`

**Expected Results**:
- Error: "Error: kimi CLI not installed..."
- No crash or unhandled exception

---

## 3. Non-Functional Requirements

### 3.1 Performance

#### TC-NF1-001: Cache Hit Latency
**Objective**: Cache hits should be significantly faster than misses

**Criteria**:
- Cache hit latency < 20% of cache miss latency
- Target: < 10 seconds for cache hit vs > 60 seconds for miss

#### TC-NF1-002: Concurrent Access
**Objective**: Multiple concurrent requests don't corrupt cache

**Steps**:
1. Send 5 simultaneous `kimi_analyze` requests for same work_dir
2. All requests complete successfully

**Expected Results**:
- Only 1 cache warming occurs
- 1 cache miss + 4 cache hits
- No duplicate session creation

### 3.2 Memory Usage

#### TC-NF2-001: Memory Leak Check
**Objective**: Verify no memory leaks during extended operation

**Steps**:
1. Run 100 iterations of create-invalidate cycles
2. Monitor memory usage

**Expected Results**:
- Memory usage remains stable
- No unbounded growth

---

## 4. Integration Requirements

### 4.1 MCP Protocol Compliance

#### TC-INT-001: Tool Discovery
**Objective**: New tools appear in MCP tool list

**Steps**:
1. Start MCP server
2. List available tools

**Expected Results**:
- `kimi_cache_status` tool is listed
- `kimi_cache_invalidate` tool is listed
- `kimi_analyze` description mentions caching

#### TC-INT-002: Response Format
**Objective**: All responses follow MCP protocol

**Expected Results**:
- All tool responses have `content` array
- Error responses have `isError: true`
- Text content uses `type: 'text'`

---

## 5. Test Environment Setup

### 5.1 Required Configuration

```json
{
  "mcpServers": {
    "kimi-code": {
      "command": "node",
      "args": ["/path/to/kimi-code-mcp/dist/index.js"],
      "env": {
        "KIMI_CACHE_DEBUG": "1"
      }
    }
  }
}
```

### 5.2 Test Codebases

| ID | Path | Type | Description |
|----|------|------|-------------|
| T1 | `/tmp/test-repo-git` | Git repo | Small TypeScript project with git history |
| T2 | `/tmp/test-repo-nogit` | Non-git | Same structure, no git |
| T3 | `/tmp/test-large-repo` | Git repo | Large codebase (>100 files) |

### 5.3 Setup Script

```bash
#!/bin/bash
# test/setup-test-env.sh

# Create test repo 1 (git)
mkdir -p /tmp/test-repo-git/src
npm init -y -f /tmp/test-repo-git
# ... add some source files
git init /tmp/test-repo-git

# Create test repo 2 (no git)
cp -r /tmp/test-repo-git /tmp/test-repo-nogit
rm -rf /tmp/test-repo-nogit/.git

# Create large test repo
mkdir -p /tmp/test-large-repo
# ... generate many files
```

---

## 6. Regression Tests

Ensure existing functionality still works:

| Test | Description |
|------|-------------|
| REG-001 | `kimi_query` without work_dir still works |
| REG-002 | `kimi_list_sessions` returns valid sessions |
| REG-003 | `kimi_resume` with explicit session_id works |
| REG-004 | `kimi_analyze` without cache (use_cache=false) works |
| REG-005 | All detail levels (summary/normal/detailed) work |

---

## 7. Test Execution Checklist

- [ ] All P0 tests pass
- [ ] All P1 tests pass
- [ ] All P2 tests pass
- [ ] Regression tests pass
- [ ] Performance benchmarks meet targets
- [ ] Memory leak test passes
- [ ] Documentation is updated
- [ ] CHANGELOG is updated

---

## 8. Known Limitations (Phase 1)

1. **No distributed cache**: Cache is in-memory only, lost on MCP restart
2. **Git dependency**: Change detection works best with git repos
3. **No prefetch**: Cache is warmed on-demand only
4. **Fixed TTL**: No adaptive expiration based on codebase activity

---

## 9. Future Test Scenarios (Phase 2+)

| Phase | Feature | Test Scenario |
|-------|---------|---------------|
| 2 | File watching | Auto-invalidate on file change |
| 2 | Prefetch | Pre-warm cache for common directories |
| 3 | Persistent cache | Cache survives MCP restart |
| 3 | Adaptive TTL | Dynamic expiration based on activity |
| 3 | Multi-level cache | L1 memory + L2 disk + L3 Kimi |

---

## Appendix: Debug Commands

```bash
# Enable debug logging
export KIMI_CACHE_DEBUG=1
node dist/index.js

# Check cache status
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"kimi_cache_status","arguments":{}}}' | node dist/index.js

# Manual test
npm run build
npm test
```
