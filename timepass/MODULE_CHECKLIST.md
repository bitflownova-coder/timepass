# 📋 Module Development Checklist

> **Purpose:** Ensure EVERY module is fully verified before marking "Complete"  
> **Required:** Check ALL boxes before updating TODO.md  
> **Last Updated:** February 1, 2026

---

## ⚠️ CRITICAL RULE

**"Complete" = Files created + Schema updated + Compiles + Tested + Verified**

**NOT** "Complete" = Files created ❌

---

## ✅ PRE-DEVELOPMENT

Before starting a new module:

- [ ] Read `.github/copilot-instructions.md`
- [ ] Read `.github/instructions/backend.instructions.md` (if backend)
- [ ] Read `.github/instructions/frontend.instructions.md` (if frontend)
- [ ] Read `.github/instructions/security.instructions.md` (if security-sensitive)
- [ ] Check `docs/DESIGN.md` for schema reference
- [ ] Check `docs/RBAC.md` for permission requirements
- [ ] Review existing similar modules for patterns

---

## 🗄️ SCHEMA CHANGES (If Applicable)

If your module requires database changes:

### Prisma Schema Updates

- [ ] Add/update models in `apps/api/prisma/schema.prisma`
- [ ] Follow naming conventions (snake_case for DB, camelCase for TS)
- [ ] Include required audit fields (`createdAt`, `createdBy`, `updatedAt`, `updatedBy`, `deletedAt`, `deletedBy`)
- [ ] Include `tenantId` on ALL tables (multi-tenancy)
- [ ] Add proper indexes (especially on `tenantId`, foreign keys)
- [ ] Add proper relations with `@relation` annotations

### Generate Prisma Client

**CRITICAL:** After ANY schema changes:

```bash
cd apps/api
npx prisma generate
```

**Verify generation succeeded:**
- [ ] Check terminal output — "Generated Prisma Client (v5.22.0) in XXXms"
- [ ] Verify types in `node_modules/@prisma/client/index.d.ts`
- [ ] Restart VS Code TS server: `Ctrl+Shift+P` → "TypeScript: Restart TS Server"

### Create Migration

```bash
cd apps/api
npx prisma migrate dev --name descriptive_migration_name
```

**Verify migration:**
- [ ] Migration file created in `apps/api/prisma/migrations/`
- [ ] Migration applied to local database
- [ ] No errors in migration output

---

## 💻 CODE DEVELOPMENT

### Backend (NestJS)

- [ ] Create module structure:
  - `{module}.module.ts`
  - `{module}.controller.ts`
  - `{module}.service.ts`
  - `dto/create-{entity}.dto.ts`
  - `dto/update-{entity}.dto.ts`
  - `dto/{entity}-response.dto.ts`

- [ ] Follow patterns from `.github/instructions/backend.instructions.md`:
  - ✅ Use guards: `@UseGuards(JwtAuthGuard, RbacGuard, TenantGuard)`
  - ✅ Use permissions: `@RequirePermissions(Permission.XXX)`
  - ✅ Use audit logging: `@AuditLog({ action: 'XXX', sensitivity: 'XXX' })`
  - ✅ Filter by `tenantId` in ALL queries
  - ✅ Use soft delete for compliance data
  - ✅ Include pagination on list endpoints
  - ✅ Emit events for side effects
  - ✅ Invalidate cache on mutations

- [ ] DTOs have proper validation:
  - `@IsString()`, `@IsEmail()`, `@IsUUID()`, etc.
  - `@IsNotEmpty()` where required
  - Swagger decorators: `@ApiProperty()`

### Frontend (Next.js)

- [ ] Create page structure:
  - `app/(dashboard)/(role)/{module}/page.tsx` (Server Component)
  - `components/modules/{module}/{module}-page-client.tsx` (Client Component)
  - Forms, tables, stats components

- [ ] Follow patterns from `.github/instructions/frontend.instructions.md`:
  - ✅ Use React Query for data fetching
  - ✅ Handle loading/error states
  - ✅ Use Zod for form validation
  - ✅ Use shadcn/ui components
  - ✅ Mobile responsive design
  - ✅ Permission guards where needed

---

## 🔍 COMPILATION VERIFICATION

**MANDATORY:** Run these commands and verify 0 errors:

### Backend TypeScript Check

```bash
cd apps/api
npx tsc --noEmit
```

**Expected output:** "No errors" or silent exit

- [ ] **Command exits with code 0**
- [ ] **NO errors printed**
- [ ] **If errors exist, FIX THEM before proceeding**

### Frontend TypeScript Check

```bash
cd apps/web
npx tsc --noEmit
```

- [ ] **Command exits with code 0**
- [ ] **NO errors printed**

### VS Code Diagnostics

- [ ] Open VS Code Problems panel (`Ctrl+Shift+M`)
- [ ] **Verify 0 errors** in your module files
- [ ] If errors exist but `tsc --noEmit` passes:
  - Restart TS server: `Ctrl+Shift+P` → "TypeScript: Restart TS Server"
  - If still errors, they're real — fix them

### Build Verification

```bash
# Backend
cd apps/api
npm run build

# Frontend
cd apps/web
npm run build
```

- [ ] Both builds succeed with no errors

---

## 🧪 TESTING

### Unit Tests

**Required for EVERY service:**

Create `{module}/__tests__/{module}.service.spec.ts`:

- [ ] Test happy path (successful operations)
- [ ] Test validation errors (invalid input)
- [ ] Test authorization (permission checks)
- [ ] Test tenant isolation (cross-tenant access denied)
- [ ] Test edge cases (concurrent requests, race conditions)
- [ ] Test error handling

**Run tests:**

```bash
cd apps/api
npm test -- {module}.service.spec.ts
```

- [ ] **ALL tests pass**
- [ ] **Coverage > 80% for new code**

### Integration Tests (Optional but Recommended)

Create `{module}/__tests__/{module}.e2e.spec.ts`:

- [ ] Test full API flow (create → read → update → delete)
- [ ] Test with real database (test environment)
- [ ] Test authentication/authorization flow

### Manual Testing

Start backend:
```bash
cd apps/api
npm run dev
```

- [ ] API starts without errors
- [ ] Test endpoints with Postman/curl
- [ ] Verify tenant isolation (try accessing other tenant's data)
- [ ] Verify permission guards (try without auth token)
- [ ] Check audit logs are created
- [ ] Check error responses are proper format

---

## 🔒 SECURITY VERIFICATION

**If module handles sensitive data (CONFIDENTIAL/RESTRICTED):**

- [ ] Data encrypted at rest (if required)
- [ ] Signed URLs for file access (if applicable)
- [ ] Time-window access controls (exam papers, etc.)
- [ ] Audit logging on ALL sensitive operations
- [ ] No PII in logs or error messages
- [ ] Permission checks at controller level (not just service)

**Refer to:** `.github/instructions/security.instructions.md`

---

## 📝 DOCUMENTATION

### Code Documentation

- [ ] Swagger decorators on all controller endpoints:
  ```typescript
  @ApiOperation({ summary: 'Brief description' })
  @ApiResponse({ status: 200, type: ResponseDto })
  @ApiResponse({ status: 404, description: 'Not found' })
  ```

- [ ] JSDoc comments on complex service methods

### Project Documentation

- [ ] Update `STATUS.md` if significant progress
- [ ] Update `docs/TODO.md` with completion status
- [ ] Add API examples to `docs/API.md` (if applicable)

---

## 🔄 GIT WORKFLOW

### Before Commit

```bash
# Check what's changed
git status
git diff

# Review changes carefully
```

- [ ] Only relevant files staged (no accidental `node_modules/`, `.env`, etc.)
- [ ] No console.log statements left in code
- [ ] No commented-out code blocks
- [ ] No TODO/FIXME comments (or create ticket for them)

### Commit

```bash
# Stage files
git add {specific-files}

# Commit with descriptive message
git commit -m "feat(module): Brief description of what was added

- Detailed bullet points
- Of significant changes
- Following conventional commit format"
```

- [ ] Pre-commit hook passes (if enabled)
- [ ] Commit message follows conventional commits format
- [ ] Commit is focused (one feature/fix per commit)

### Push

```bash
git push origin feature/your-branch-name
```

- [ ] CI/CD workflow passes (once implemented)
- [ ] No build errors in GitHub Actions

---

## ✅ FINAL CHECKLIST

**BEFORE marking as "Complete" in TODO.md:**

- [ ] **Schema:** Prisma client regenerated (if schema changed)
- [ ] **Compilation:** `npx tsc --noEmit` shows 0 errors (backend)
- [ ] **Compilation:** `npx tsc --noEmit` shows 0 errors (frontend, if applicable)
- [ ] **VS Code:** Problems panel shows 0 errors
- [ ] **Build:** `npm run build` succeeds for both apps
- [ ] **Tests:** Unit tests written and passing (>80% coverage)
- [ ] **Manual Test:** Backend starts, endpoints work
- [ ] **Security:** Security checks passed (if sensitive data)
- [ ] **Documentation:** Swagger docs updated, STATUS.md updated
- [ ] **Git:** Changes committed, pushed, CI passes

---

## 🚫 ANTI-PATTERNS (NEVER DO)

❌ **Mark "Complete" without running `tsc --noEmit`**
❌ **Skip `npx prisma generate` after schema changes**
❌ **Commit code with TypeScript errors**
❌ **Write services without tests**
❌ **Skip permission guards on endpoints**
❌ **Hardcode tenant IDs or skip tenant filtering**
❌ **Store secrets in code**
❌ **Skip audit logging on sensitive operations**
❌ **Use `any` type in TypeScript**
❌ **Trust user input without validation**

---

## 📊 QUALITY GATES

**Module CANNOT be marked "Complete" if:**

- ❌ TypeScript has compilation errors
- ❌ Tests are not written
- ❌ Tests are failing
- ❌ Coverage < 80%
- ❌ Builds fail
- ❌ VS Code shows errors
- ❌ Security checks not done (for sensitive modules)
- ❌ Manual testing not performed

**Only mark "Complete" when ALL quality gates pass.**

---

## 🎯 TEMPLATE: TODO.md Update

When marking complete, update TODO.md like this:

```markdown
| P2-XXX | ✅ {Module Name} Module | P0 | L | ✅ VERIFIED | Dev | Feb 1, 2026 |
```

**Add "VERIFIED" to distinguish from old "DONE" (files only).**

---

## 📞 NEED HELP?

- **Backend patterns:** `.github/instructions/backend.instructions.md`
- **Frontend patterns:** `.github/instructions/frontend.instructions.md`
- **Security patterns:** `.github/instructions/security.instructions.md`
- **RBAC reference:** `docs/RBAC.md`
- **Schema reference:** `docs/DESIGN.md`
- **Common mistakes:** `.github/COMMON_MISTAKES.md`

---

**Remember:** "Complete" means **verified working**, not just "files created".

✅ **Follow this checklist for EVERY module** to prevent issues like the "193 errors" incident.
