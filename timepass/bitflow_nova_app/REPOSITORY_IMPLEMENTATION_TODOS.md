# Repository Implementation TODOs

## Overview
The "Don't Make Me Think" refactor is complete at the database and UI layers. The following repository methods need full implementations to connect everything together.

---

## Priority 1: Core Auto-Learning Methods

### In TransactionRepository Interface

#### 1. Learning Rule Methods (CRITICAL)
```kotlin
// Already defined in interface, need implementation in TransactionRepositoryImpl

suspend fun insertLearningRule(rule: CategoryLearningRule)
suspend fun updateLearningRule(rule: CategoryLearningRule)
suspend fun findLearningRule(pattern: String): CategoryLearningRule?
fun getAllLearningRules(): Flow<List<CategoryLearningRule>>
suspend fun updateLearningRulesForCategory(oldCategoryId: Long, newCategoryId: Long)
suspend fun deleteLearningRulesForCategory(categoryId: Long)
```

**Implementation Note**: These should directly call `learningRuleDao` methods. Need to convert between domain models (`CategoryLearningRule`) and entities (`LearningRuleEntity`).

**Conversion Functions Needed:**
```kotlin
// In TransactionRepositoryImpl.kt

private fun CategoryLearningRule.toEntity() = LearningRuleEntity(
    id = this.id,
    merchantPattern = this.descriptionPattern,
    categoryId = this.categoryId,
    confidenceScore = this.confidenceScore,
    usageCount = this.usageCount,
    createdAt = this.createdAt,
    lastUsedAt = this.lastAppliedAt
)

private fun LearningRuleEntity.toDomain() = CategoryLearningRule(
    id = this.id,
    descriptionPattern = this.merchantPattern,
    categoryId = this.categoryId,
    confidenceScore = this.confidenceScore,
    usageCount = this.usageCount,
    createdAt = this.createdAt,
    lastAppliedAt = this.lastUsedAt,
    createdByUserCorrection = true
)
```

---

## Priority 2: Daily Pulse Calculation Methods

### In TransactionRepository Interface

#### 2. Monthly Income Calculation
```kotlin
suspend fun getMonthlyIncome(startDate: LocalDate, endDate: LocalDate): Double
```

**Implementation:**
```kotlin
override suspend fun getMonthlyIncome(startDate: LocalDate, endDate: LocalDate): Double {
    return transactionDao.getTransactionsInPeriod(startDate, endDate)
        .first() // Get current value from Flow
        .filter { it.direction == TransactionDirection.CREDIT }
        .sumOf { it.amount }
}
```

---

#### 3. Today's Expenses
```kotlin
suspend fun getTodayExpenses(date: LocalDate): Double
```

**Implementation:**
```kotlin
override suspend fun getTodayExpenses(date: LocalDate): Double {
    return transactionDao.getTransactionsInPeriod(date, date)
        .first()
        .filter { it.direction == TransactionDirection.DEBIT }
        .sumOf { it.amount }
}
```

---

#### 4. Month-to-Date Expenses
```kotlin
suspend fun getMonthExpenses(startDate: LocalDate, endDate: LocalDate): Double
```

**Implementation:**
```kotlin
override suspend fun getMonthExpenses(startDate: LocalDate, endDate: LocalDate): Double {
    return transactionDao.getTransactionsInPeriod(startDate, endDate)
        .first()
        .filter { it.direction == TransactionDirection.DEBIT }
        .sumOf { it.amount }
}
```

---

#### 5. Fixed Expenses (Subscriptions)
```kotlin
suspend fun getFixedExpenses(): Double
```

**Implementation Note**: This needs a new `RecurringPatternEntity` and DAO to store confirmed subscriptions.

**Temporary Implementation:**
```kotlin
override suspend fun getFixedExpenses(): Double {
    // TODO: Sum confirmed subscriptions
    // For now, return 0 and let user manually set in settings
    return 0.0
}
```

---

#### 6. Savings Goal
```kotlin
suspend fun getSavingsGoal(): Double
```

**Implementation Note**: This should be stored in user preferences/settings.

**Temporary Implementation:**
```kotlin
override suspend fun getSavingsGoal(): Double {
    // TODO: Get from SharedPreferences or Settings table
    return 10000.0 // Default: ₹10,000
}
```

---

## Priority 3: Category Management Methods

### In TransactionRepository Interface

#### 7. Category Merge
```kotlin
suspend fun mergeCategories(fromCategoryId: Long, toCategoryId: Long)
```

**Implementation:**
```kotlin
override suspend fun mergeCategories(fromCategoryId: Long, toCategoryId: Long) {
    // Update all transactions
    transactionDao.updateTransactionsCategory(fromCategoryId, toCategoryId)
    
    // Update learning rules
    learningRuleDao.updateRulesCategory(fromCategoryId, toCategoryId)
    
    // Increment target category usage count by source category count
    val fromCategory = categoryDao.getCategoryById(fromCategoryId)
    val toCategory = categoryDao.getCategoryById(toCategoryId)
    if (fromCategory != null && toCategory != null) {
        categoryDao.insertCategory(
            toCategory.copy(usageCount = toCategory.usageCount + fromCategory.usageCount)
        )
    }
}
```

---

#### 8. Uncategorize Activities
```kotlin
suspend fun uncategorizeActivities(categoryId: Long)
```

**Implementation Note**: Need to create an "Uncategorized" category with special ID (e.g., 0 or -1).

**Implementation:**
```kotlin
override suspend fun uncategorizeActivities(categoryId: Long) {
    val uncategorizedId = 0L // Special ID for uncategorized
    transactionDao.updateTransactionsCategory(categoryId, uncategorizedId)
}
```

---

#### 9. Delete Transaction (with Undo Support)
```kotlin
suspend fun deleteTransaction(activityId: Long)
```

**Implementation:**
```kotlin
override suspend fun deleteTransaction(activityId: Long) {
    transactionDao.deleteTransaction(activityId)
    
    // TODO: Implement undo stack
    // For now, direct delete
}
```

---

## Priority 4: Subscription Detection Methods

### In TransactionRepository Interface

#### 10. Get Transactions for Subscription Detection
```kotlin
suspend fun getTransactionsForSubscriptionDetection(startDate: LocalDate): List<TransactionEntity>
```

**Implementation:**
```kotlin
override suspend fun getTransactionsForSubscriptionDetection(startDate: LocalDate): List<TransactionEntity> {
    return transactionDao.getTransactionsForSubscriptionDetection(startDate)
}
```

---

#### 11. Confirm Subscription
```kotlin
suspend fun confirmSubscription(pattern: RecurringPattern)
```

**Implementation Note**: This needs a new `RecurringPatternEntity` table.

**Temporary Implementation:**
```kotlin
override suspend fun confirmSubscription(pattern: RecurringPattern) {
    // TODO: Save to recurring_patterns table
    // For now, just log
    Log.d("TransactionRepository", "Confirmed subscription: ${pattern.merchantName}")
}
```

---

## Priority 5: Missing Domain Models

### RecurringPattern (Already exists in domain)
**File**: `domain/model/RecurringPattern.kt`

Check if this exists. If not, create:

```kotlin
package com.bitflow.finance.domain.model

import java.time.LocalDate

data class RecurringPattern(
    val id: Long = 0,
    val merchantName: String,
    val averageAmount: Double,
    val frequency: String, // "Daily", "Weekly", "Monthly", "Yearly"
    val intervalDays: Int,
    val occurrenceCount: Int,
    val lastTransactionDate: LocalDate,
    val nextExpectedDate: LocalDate,
    val confidenceScore: Float,
    val isConfirmedSubscription: Boolean = false,
    val categoryId: Long?
)
```

---

### CategoryLearningRule (Already exists in domain)
**File**: `domain/model/CategoryLearningRule.kt`

Verify it matches the entity structure. Update if needed:

```kotlin
package com.bitflow.finance.domain.model

import java.time.LocalDateTime

data class CategoryLearningRule(
    val id: Long = 0,
    val descriptionPattern: String,
    val categoryId: Long,
    val confidenceScore: Float,
    val usageCount: Int,
    val createdAt: LocalDateTime = LocalDateTime.now(),
    val lastAppliedAt: LocalDateTime = LocalDateTime.now(),
    val createdByUserCorrection: Boolean = true
)
```

---

## Implementation Order

### Week 1: Core Functionality
1. ✅ Learning rule conversions (toEntity/toDomain)
2. ✅ Insert/Update/Find learning rules
3. ✅ Category merge logic
4. ✅ Delete with learning rule cleanup

### Week 2: Daily Pulse
1. ⏳ Monthly income calculation
2. ⏳ Today's expenses
3. ⏳ Month-to-date expenses
4. ⏳ Create Settings entity for savings goal

### Week 3: Subscriptions
1. ⏳ Create RecurringPatternEntity
2. ⏳ Create RecurringPatternDao
3. ⏳ Implement confirmSubscription
4. ⏳ Implement getFixedExpenses (sum confirmed subscriptions)

### Week 4: Polish
1. ⏳ Undo stack for deletions
2. ⏳ Transaction export with learning rules
3. ⏳ Bulk operations optimization
4. ⏳ Error handling and edge cases

---

## Testing Checklist

### Auto-Learning
- [ ] Create transaction with merchant name
- [ ] Manually categorize
- [ ] Verify learning rule created
- [ ] Create similar transaction
- [ ] Verify auto-categorization
- [ ] Change category
- [ ] Verify confidence updated

### Daily Pulse
- [ ] Add income transactions
- [ ] Add expense transactions
- [ ] Verify safe-to-spend calculation
- [ ] Test edge case: No income
- [ ] Test edge case: Last day of month
- [ ] Test edge case: Overspent

### Category Merge
- [ ] Create category with 10 transactions
- [ ] Merge with another category
- [ ] Verify all 10 transactions moved
- [ ] Verify learning rules updated
- [ ] Verify usage counts added
- [ ] Verify source category deleted

### Subscription Detection
- [ ] Create 3 monthly payments to same merchant
- [ ] Run detection algorithm
- [ ] Verify pattern detected
- [ ] Verify confidence score > 0.7
- [ ] Confirm subscription
- [ ] Verify saved in database

---

## Quick Start Commands

### Run Database Migration
```kotlin
// In AppDatabaseTest.kt or manual test

val db = Room.databaseBuilder(context, AppDatabase::class.java, "finance_test")
    .addMigrations(AppDatabase.MIGRATION_2_3)
    .build()

// Verify tables exist
db.query("SELECT name FROM sqlite_master WHERE type='table'").use { cursor ->
    while (cursor.moveToNext()) {
        println("Table: ${cursor.getString(0)}")
    }
}

// Should see: categories, transactions, learning_rules, accounts
```

### Test Auto-Learning Flow
```kotlin
// In AddActivityViewModel test

val viewModel = AddActivityViewModel(repository, autoLearnUseCase)

// Simulate user entry
viewModel.updateAmount("50")
viewModel.updateNote("Netflix")
// Should auto-select Entertainment category if learned

viewModel.selectCategory(foodCategory)
viewModel.saveActivity()
// Should create learning rule linking "netflix" to Food (if manually changed)
```

---

## Notes for Junior Developers

### Common Pitfalls
1. **Don't forget Flow vs suspend**: Queries returning Flow are reactive, suspend functions are one-shot
2. **Test migrations**: Always test database migrations with actual data
3. **Domain vs Entity**: Never expose entities to UI layer, always convert to domain models
4. **Confidence scoring**: Don't make it too aggressive (0.8+) initially, users need time to correct

### Useful Debugging
```kotlin
// Log learning rules
learningRuleDao.getAllRules().collect { rules ->
    rules.forEach { rule ->
        Log.d("Learning", "${rule.merchantPattern} → ${rule.categoryId} (${rule.confidenceScore})")
    }
}

// Log category usage
categoryDao.getAllCategories().collect { categories ->
    categories.forEach { cat ->
        Log.d("Categories", "${cat.name}: ${cat.usageCount} uses")
    }
}
```

---

## Questions? Ask These:

1. "Should auto-categorization be opt-in or opt-out?"
   → **Opt-out** (it's invisible, just works)

2. "What if learning rule conflicts (same merchant, different categories)?"
   → **Last correction wins** (user's most recent choice)

3. "How to handle category deletion with many transactions?"
   → **Always ask for merge target** (never silent delete)

4. "Should we show confidence scores to users?"
   → **No** (keep it invisible, they just see it works)

---

This completes the TODO list for connecting all the pieces! 🎉
