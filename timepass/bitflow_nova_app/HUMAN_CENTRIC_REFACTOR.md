# Finance App - Human-Centric Refactor Documentation

## 🎯 Philosophy: "Don't Make Me Think"

This refactor transforms a technically-sound finance app into an intuitive, human-friendly experience that a student or non-tech parent can use effortlessly.

---

## 📱 UI Screen Flow (Updated)

### **1. Home Screen (Peace of Mind Dashboard)**

**Purpose**: Give users instant confidence about their finances

**Components**:
- **Daily Pulse Card** (replaces Net Worth)
  - Large, color-coded card (Green/Yellow/Red)
  - Shows: "You can spend ₹1,200 today and still save money"
  - Visual gauge showing spending progress
  - No complex charts or percentages
  
- **Subscription Detective Cards**
  - Auto-detected recurring payments
  - "We noticed a monthly ₹199 payment to Netflix. Is this a subscription?"
  - Two buttons: [No, Ignore] [Yes, Track it]
  
- **Recent Activity** (simplified list)
  - Clean, scannable list
  - Category emoji, description, amount
  - Color-coded: Red (Expense), Green (Income)

**Actions**:
- FAB (+) → Add Activity Screen
- "View Insights" → Insights Screen
- Privacy toggle (eye icon) → Blur amounts

---

### **2. Add Activity Screen (Speed is King)**

**Design Philosophy**: Type → Tap → Done. No confirmation needed.

**Layout** (Single Page):

```
┌─────────────────────────────────────┐
│  [Back]    Add Activity             │
├─────────────────────────────────────┤
│                                     │
│     [Expense] [Income]  ← Toggle    │
│                                     │
│          ₹  1,250      ← Big        │
│                                     │
├─────────────────────────────────────┤
│  Choose Category                    │
│                                     │
│  🍔    🚗    🏠    💊               │
│  Food  Travel Home  Health          │
│                                     │
│  👕    📱    🎬    ...              │
│  Shop  Phone Movies More            │
│                                     │
├─────────────────────────────────────┤
│  Note (Optional)                    │
│  [            ]                     │
│                                     │
│  Date: [📅 Today ▼]                │
│                                     │
├─────────────────────────────────────┤
│         Custom Numpad               │
│                                     │
│      [1] [2] [3]                    │
│      [4] [5] [6]                    │
│      [7] [8] [9]                    │
│      [.] [0] [⌫]                    │
│                                     │
└─────────────────────────────────────┘
```

**Behavior**:
1. User types amount → Taps category
2. **Activity auto-saves immediately** (no confirm button)
3. Screen closes, shows success toast
4. If user wants to add note/date, they enter before tapping category

**Key Innovation**:
- Categories sorted by usage (most used first)
- Only show top 8 + "More" button
- Large touch targets (friendly for all ages)

---

### **3. Insights Screen** (renamed from Analytics)

**Purpose**: Discover spending patterns, not intimidate with charts

**Components**:
- Monthly spending by category (simple bar chart)
- "Your top 3 spending categories this month"
- "You spent ₹2,500 less than last month 🎉"
- Trends in plain English, not graphs

---

### **4. Manage Categories Screen**

**Purpose**: User has full control. No "system" restrictions.

**Features**:
- All categories sorted by usage count
- Any category can be deleted
- When deleting, show merge dialog:
  - "You have 45 activities in 'Food'. What should we do?"
  - Option 1: Move to [Select Category]
  - Option 2: Mark as Uncategorized
- Hide/Show toggle (instead of delete)
- Edit emoji and name

---

### **5. Settings Screen**

**Simplified Options**:
- Currency
- Privacy Mode (default off)
- **PIN Lock** (moved from onboarding)
- Categories → Manage Categories screen
- Import Statement
- Export Data
- About

**Removed**:
- Shake-to-blur (replaced with privacy toggle)
- Smart Rules screen (now invisible)
- Complex budget setup

---

## 🧠 Revised Data Logic

### **1. Activity Model** (formerly Transaction)

```kotlin
data class Activity(
    val id: Long,
    val accountId: Long,
    val activityDate: LocalDate,
    val description: String,
    val amount: Double,
    val type: ActivityType, // EXPENSE, INCOME, TRANSFER
    val categoryId: Long?,
    val notes: String?,
    
    // Auto-learning fields
    val isAutoCategorized: Boolean = false,
    val confidenceScore: Float? = null // 0.0 to 1.0
)

enum class ActivityType {
    EXPENSE,  // Was "DEBIT"
    INCOME,   // Was "CREDIT"
    TRANSFER
}
```

---

### **2. Category Model** (Enhanced)

```kotlin
data class Category(
    val id: Long,
    val name: String,
    val type: CategoryType,
    val icon: String, // Emoji (🍔) or icon name
    val color: Int,
    
    // Smart sorting
    val usageCount: Int = 0,
    val lastUsedAt: Long? = null,
    
    // User control
    val isUserDeletable: Boolean = true, // No "system" categories
    val isHidden: Boolean = false,
    val sortOrder: Int = 0 // Auto-calculated from usageCount
)
```

**Sorting Logic**:
```kotlin
categories.sortedWith(
    compareByDescending { it.usageCount }
        .thenByDescending { it.lastUsedAt }
)
```

---

### **3. Auto-Learning System** (Invisible)

**Components**:

**a) CategoryLearningRule** (Never shown to user)
```kotlin
data class CategoryLearningRule(
    val id: Long,
    val descriptionPattern: String, // e.g., "netflix"
    val categoryId: Long,
    val confidenceScore: Float, // 0.0 to 1.0
    val usageCount: Int,
    val createdByUserCorrection: Boolean = true
)
```

**b) Learning Workflow**:

1. **User imports statement** → Auto-categorize using existing rules
2. **User corrects a category** on an activity
3. **System silently creates/updates rule**
4. **Show toast**: "Got it! Future Netflix payments → Entertainment" [Undo]
5. **Next import** → Rule auto-applies

**Example**:
```
User changes "UPI/Netflix" from "Bills" → "Entertainment"

System creates:
CategoryLearningRule(
    descriptionPattern = "netflix",
    categoryId = 12, // Entertainment
    confidenceScore = 0.8
)

Next statement with "Netflix" → Auto-categorized to Entertainment
```

**Pattern Extraction**:
```kotlin
// From: "UPI/DR/203290292730/NETFLIX/BKID/..."
// Extract: "netflix"

fun extractPattern(description: String): String {
    return description
        .replace(Regex("UPI/(CR|DR)/\\d+/"), "")
        .split("/")
        .firstOrNull { it.length > 3 }
        ?.lowercase()
        ?: ""
}
```

---

### **4. Daily Pulse Calculation**

**Formula**:
```kotlin
Monthly Income:     ₹50,000
Fixed Expenses:     ₹15,000 (rent, subscriptions)
Savings Goal (20%): ₹10,000
───────────────────────────
Available:          ₹25,000
Daily Budget:       ₹25,000 / 30 = ₹833

Today Spent:        ₹250
Safe to Spend:      ₹833 - ₹250 = ₹583
```

**Status Logic**:
```kotlin
val progress = todaySpent / dailyBudget

when {
    progress < 0.5  -> GREAT      (Green)
    progress < 0.75 -> GOOD       (Green)
    progress < 1.0  -> CAUTION    (Yellow)
    else            -> SLOW_DOWN  (Red)
}
```

---

### **5. Subscription Detective**

**Detection Logic**:

1. **Group activities by merchant**
```kotlin
val groups = activities.groupBy { extractMerchant(it.description) }
```

2. **Analyze each group**:
   - Need ≥ 2 occurrences
   - Calculate intervals between payments
   - Determine frequency:
     - ~1 day apart → Daily
     - ~7 days → Weekly
     - ~30 days → Monthly
     - ~365 days → Yearly
   - Check amount consistency (within 10% variance)

3. **Create detection card**:
```kotlin
SubscriptionDetectionCard(
    merchantName = "Netflix",
    amount = 199.0,
    frequency = "monthly",
    lastPaymentDate = LocalDate.now()
)
```

4. **Show on Home Screen**:
   - Only unconfirmed patterns
   - User clicks [Yes] → Mark as confirmed subscription
   - User clicks [No] → Dismiss forever

---

## 🔄 Migration Path (Existing App → Human-Centric)

### **Phase 1: Data Model Migration**
1. Add new columns to database:
   ```sql
   ALTER TABLE transactions ADD COLUMN is_auto_categorized BOOLEAN DEFAULT 0;
   ALTER TABLE transactions ADD COLUMN confidence_score REAL;
   
   ALTER TABLE categories ADD COLUMN usage_count INTEGER DEFAULT 0;
   ALTER TABLE categories ADD COLUMN last_used_at INTEGER;
   ALTER TABLE categories ADD COLUMN is_user_deletable BOOLEAN DEFAULT 1;
   ALTER TABLE categories ADD COLUMN is_hidden BOOLEAN DEFAULT 0;
   ```

2. Create new tables:
   ```sql
   CREATE TABLE category_learning_rules (
       id INTEGER PRIMARY KEY,
       description_pattern TEXT NOT NULL,
       category_id INTEGER NOT NULL,
       confidence_score REAL DEFAULT 0.8,
       usage_count INTEGER DEFAULT 0,
       created_at INTEGER NOT NULL
   );
   
   CREATE TABLE recurring_patterns (
       id INTEGER PRIMARY KEY,
       merchant_name TEXT NOT NULL,
       average_amount REAL NOT NULL,
       frequency TEXT NOT NULL,
       occurrence_count INTEGER NOT NULL,
       is_confirmed_subscription BOOLEAN DEFAULT 0,
       is_dismissed BOOLEAN DEFAULT 0
   );
   ```

3. Backfill usage counts:
   ```kotlin
   // Count existing usage for each category
   categories.forEach { category ->
       val count = activities.count { it.categoryId == category.id }
       updateCategoryUsageCount(category.id, count)
   }
   ```

### **Phase 2: UI Gradual Rollout**
1. Keep old screens, add new ones alongside
2. Add feature flag: `USE_HUMAN_CENTRIC_UI = true`
3. Test with beta users
4. Remove old screens after validation

### **Phase 3: Remove Old Features**
- Delete "Smart Rules" screen
- Remove shake-to-blur sensor code
- Simplify settings

---

## 🎨 Design Tokens

### **Colors** (Human-friendly)
```kotlin
Expense:  Color(0xFFEF5350) // Soft red
Income:   Color(0xFF66BB6A) // Friendly green
Transfer: Color(0xFF42A5F5) // Calm blue

PulseGreen:  Color(0xFF66BB6A)
PulseYellow: Color(0xFFFFA726)
PulseRed:    Color(0xFFEF5350)
```

### **Typography**
```kotlin
Display (Amount): 56.sp, Bold
Title:            20.sp, SemiBold
Body:             16.sp, Regular
Caption:          14.sp, Regular
```

### **Spacing**
```kotlin
Screen padding:   16.dp
Card padding:     24.dp
Item spacing:     12.dp
Section spacing:  24.dp
```

---

## 🚀 Implementation Checklist

- [x] Create new `Activity` and `ActivityType` models
- [x] Enhance `Category` with usage tracking
- [x] Build `AddActivityScreen` with custom numpad
- [x] Implement `CategoryManagementScreen` with merge logic
- [x] Create `CategoryLearningRule` system
- [x] Build `AutoLearnCategoryUseCase`
- [x] Design `DailyPulse` calculation logic
- [x] Create new `HomeScreenV2` with Pulse gauge
- [x] Implement `DetectSubscriptionsUseCase`
- [x] Update navigation labels (Analytics → Insights)
- [ ] Update database with migration scripts
- [ ] Update repository interfaces with new methods
- [ ] Add unit tests for auto-learning
- [ ] Add unit tests for subscription detection
- [ ] Update onboarding (remove PIN, allow exploration)
- [ ] Remove shake-to-blur sensor code
- [ ] Add feedback toasts with undo actions
- [ ] Implement date picker for AddActivity
- [ ] Add category editor dialog
- [ ] Update import flow to use auto-learning

---

## 📖 Usage Examples

### **Example 1: Adding an Expense**
```
1. User taps FAB (+)
2. Types "150" on numpad
3. Taps "Food 🍔" category
4. ✅ Activity auto-saves, screen closes
5. Toast: "₹150 added to Food"
```

### **Example 2: Learning from Correction**
```
1. User sees imported activity: "UPI/Netflix" → Bills
2. Taps activity → Opens detail screen
3. Changes category to "Entertainment"
4. Toast: "Got it! Future Netflix → Entertainment" [Undo]
5. Rule created silently in background
6. Next month: Netflix auto-categorized to Entertainment
```

### **Example 3: Subscription Detection**
```
1. User imports 3 months of statements
2. System detects: Netflix ₹199 every 30 days
3. Home screen shows card:
   "We noticed a monthly ₹199 payment to Netflix. 
    Is this a subscription?"
    [No, Ignore] [Yes, Track it]
4. User taps "Yes, Track it"
5. Card disappears, subscription saved
6. Future Netflix payments tagged automatically
```

---

## 🎓 Design Principles Applied

1. **Speed is King**: Single-page add flow, auto-save
2. **Invisible Intelligence**: Learning happens silently
3. **Natural Language**: "Activity" not "Transaction"
4. **Peace of Mind**: Daily Pulse not complex budgets
5. **User Control**: Delete any category, no system locks
6. **Smart Defaults**: Today's date, most-used categories
7. **Undo Everything**: Toast with undo button
8. **Progressive Disclosure**: Hide complexity until needed

---

## 📊 Success Metrics

**Before (Engineered)**:
- 3-step add flow
- Manual rule creation
- Complex budget screens
- 15+ taps to add expense

**After (Human-Centric)**:
- 1-page add flow
- Automatic learning
- Simple "Safe to Spend" metric
- 3 taps to add expense

**Target**:
- 50% reduction in time to add activity
- 80% of categories auto-learned within 1 month
- 90% subscription detection accuracy
- Zero user complaints about "system" categories

---

## 🔧 Technical Architecture

```
UI Layer (Compose)
├── HomeScreenV2
├── AddActivityScreen
├── CategoryManagementScreen
└── InsightsScreen

ViewModel Layer
├── HomeViewModelV2
├── AddActivityViewModel
└── CategoryManagementViewModel

Domain Layer (Use Cases)
├── AutoLearnCategoryUseCase
├── DetectSubscriptionsUseCase
└── CalculateDailyPulseUseCase

Repository Layer
├── TransactionRepository
│   ├── insertActivity()
│   ├── autoCategorizeBatch()
│   ├── learnFromCorrection()
│   └── detectSubscriptions()
└── CategoryRepository
    ├── incrementUsageCount()
    ├── mergeCategories()
    └── getSortedByUsage()

Data Layer (Room)
├── ActivityEntity
├── CategoryEntity
├── CategoryLearningRuleEntity
└── RecurringPatternEntity
```

---

## 🎯 Next Steps

1. **Immediate**: Update repository interfaces with new methods
2. **Week 1**: Implement database migrations
3. **Week 2**: Add unit tests for core logic
4. **Week 3**: Beta test with 5-10 users
5. **Week 4**: Roll out to production

---

**Key Takeaway**: We transformed a technically sound app into one your grandmother could use confidently. That's human-centric design. 🎉
