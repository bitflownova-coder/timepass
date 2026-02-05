package com.bitflow.finance.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.bitflow.finance.data.local.dao.AccountDao
import com.bitflow.finance.data.local.dao.CategoryDao
import com.bitflow.finance.data.local.dao.LearningRuleDao
import com.bitflow.finance.data.local.dao.TransactionDao
import com.bitflow.finance.data.local.dao.InvoiceDao
import com.bitflow.finance.data.local.dao.UserAccountDao
import com.bitflow.finance.data.local.dao.FriendDao
import com.bitflow.finance.data.local.dao.SplitDao
import com.bitflow.finance.data.local.dao.SavingsGoalDao
import com.bitflow.finance.data.local.dao.BillReminderDao
import com.bitflow.finance.data.local.dao.TransactionTemplateDao
import com.bitflow.finance.data.local.dao.ClientDao
import com.bitflow.finance.data.local.dao.DebtDao
import com.bitflow.finance.data.local.dao.HoldingDao
import com.bitflow.finance.data.local.dao.RecurringPatternDao
import com.bitflow.finance.data.local.entity.AccountEntity
import com.bitflow.finance.data.local.entity.CategoryEntity
import com.bitflow.finance.data.local.entity.LearningRuleEntity
import com.bitflow.finance.data.local.entity.TransactionEntity
import com.bitflow.finance.data.local.entity.InvoiceEntity
import com.bitflow.finance.data.local.entity.UserAccountEntity
import com.bitflow.finance.data.local.entity.FriendEntity
import com.bitflow.finance.data.local.entity.SplitGroupEntity
import com.bitflow.finance.data.local.entity.SplitGroupMemberEntity
import com.bitflow.finance.data.local.entity.SplitExpenseEntity
import com.bitflow.finance.data.local.entity.SplitExpenseShareEntity
import com.bitflow.finance.data.local.entity.SavingsGoalEntity
import com.bitflow.finance.data.local.entity.BillReminderEntity
import com.bitflow.finance.data.local.entity.TransactionTemplateEntity
import com.bitflow.finance.data.local.entity.ClientEntity
import com.bitflow.finance.data.local.entity.DebtEntity
import com.bitflow.finance.data.local.entity.HoldingEntity
import com.bitflow.finance.data.local.entity.RecurringPatternEntity


@Database(
    entities = [
        AccountEntity::class, 
        TransactionEntity::class, 
        CategoryEntity::class,
        LearningRuleEntity::class,
        InvoiceEntity::class,
        UserAccountEntity::class,
        FriendEntity::class,
        SplitGroupEntity::class,
        SplitGroupMemberEntity::class,
        SplitExpenseEntity::class,
        SplitExpenseShareEntity::class,
        SavingsGoalEntity::class,
        BillReminderEntity::class,
        TransactionTemplateEntity::class,
        ClientEntity::class,
        DebtEntity::class,
        HoldingEntity::class,
        RecurringPatternEntity::class,
        com.bitflow.finance.data.local.entity.TransactionAuditLogEntity::class,
        com.bitflow.finance.data.local.entity.CrawlSessionEntity::class
    ],
    version = 27,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun accountDao(): AccountDao
    abstract fun transactionDao(): TransactionDao
    abstract fun categoryDao(): CategoryDao
    abstract fun learningRuleDao(): LearningRuleDao
    abstract fun invoiceDao(): InvoiceDao
    abstract fun userAccountDao(): UserAccountDao
    abstract fun friendDao(): FriendDao
    abstract fun splitDao(): SplitDao
    abstract fun savingsGoalDao(): SavingsGoalDao
    abstract fun billReminderDao(): BillReminderDao
    abstract fun transactionTemplateDao(): TransactionTemplateDao
    abstract fun clientDao(): ClientDao
    abstract fun debtDao(): DebtDao
    abstract fun holdingDao(): HoldingDao
    abstract fun recurringPatternDao(): RecurringPatternDao
    abstract fun transactionAuditDao(): com.bitflow.finance.data.local.dao.TransactionAuditDao
    abstract fun crawlSessionDao(): com.bitflow.finance.data.local.dao.CrawlSessionDao
    
    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: android.content.Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = androidx.room.Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "finance_app_db"
                )
                .addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5, MIGRATION_5_6, MIGRATION_6_7, MIGRATION_7_8, MIGRATION_8_9, MIGRATION_9_10, MIGRATION_10_11, MIGRATION_11_12, MIGRATION_12_13, MIGRATION_13_14, MIGRATION_14_15, MIGRATION_15_16, MIGRATION_16_17, MIGRATION_17_18, MIGRATION_18_19, MIGRATION_19_20, MIGRATION_20_21, MIGRATION_21_22, MIGRATION_22_23, MIGRATION_23_24, MIGRATION_24_25, MIGRATION_25_26, MIGRATION_26_27)
                .build()
                INSTANCE = instance
                instance
            }
        }
        // Built-in Indian expense categories - accessible to all users (userId = NULL)
        val BUILT_IN_CATEGORIES = listOf(
            // Food & Dining
            Triple("Groceries", "🛒", "#4CAF50"),
            Triple("Vegetables", "🥬", "#66BB6A"),
            Triple("Fruits", "🍎", "#FF6B6B"),
            Triple("Milk & Dairy", "🥛", "#FFFFFF"),
            Triple("Eating Out", "🍽️", "#FF5722"),
            Triple("Chai/Coffee", "☕", "#795548"),
            Triple("Street Food", "🍲", "#FFA726"),
            Triple("Sweets", "🍬", "#E91E63"),
            
            // Transportation
            Triple("Fuel/Petrol", "⛽", "#F44336"),
            Triple("Auto/Taxi", "🚕", "#FFC107"),
            Triple("Bus/Metro", "🚌", "#9C27B0"),
            Triple("Train", "🚆", "#3F51B5"),
            Triple("Two-Wheeler", "🏍️", "#FF9800"),
            
            // Utilities & Bills
            Triple("Electricity", "💡", "#FFEB3B"),
            Triple("Water Bill", "💧", "#2196F3"),
            Triple("Gas Cylinder", "🔥", "#FF5722"),
            Triple("Mobile Recharge", "📱", "#00BCD4"),
            Triple("Internet/WiFi", "📡", "#009688"),
            Triple("DTH/Cable", "📺", "#673AB7"),
            Triple("Rent", "🏠", "#8D6E63"),
            
            // Shopping & Personal
            Triple("Clothing", "👕", "#E91E63"),
            Triple("Footwear", "👟", "#9C27B0"),
            Triple("Personal Care", "💄", "#F06292"),
            Triple("Salon/Grooming", "💇", "#BA68C8"),
            Triple("Shopping", "🛍️", "#AB47BC"),
            
            // Health & Medical
            Triple("Medicine", "💊", "#00BCD4"),
            Triple("Doctor Visit", "🩺", "#26C6DA"),
            Triple("Medical Tests", "🏥", "#4DD0E1"),
            
            // Education
            Triple("School/College", "🎓", "#3F51B5"),
            Triple("Books/Stationery", "📚", "#5C6BC0"),
            Triple("Tuition", "📖", "#7E57C2"),
            
            // Entertainment
            Triple("Movies", "🎬", "#F44336"),
            Triple("Streaming", "📱", "#E91E63"),
            Triple("Games", "🎮", "#9C27B0"),
            
            // Financial
            Triple("UPI Transfer", "💸", "#607D8B"),
            Triple("Savings", "💰", "#4CAF50"),
            Triple("Investment", "📈", "#8BC34A"),
            Triple("EMI", "💳", "#FF9800"),
            Triple("Insurance", "🛡️", "#009688"),
            
            // Others
            Triple("Gifts", "🎁", "#E91E63"),
            Triple("Donations", "🙏", "#FF9800"),
            Triple("Pet Care", "🐕", "#8D6E63"),
            Triple("Home Maintenance", "🔧", "#607D8B"),
            Triple("Other", "📋", "#9E9E9E")
        )
        
        fun insertBuiltInCategories(database: androidx.sqlite.db.SupportSQLiteDatabase) {
            for ((name, icon, color) in BUILT_IN_CATEGORIES) {
                try {
                    // Insert with NULL userId (built-in category accessible to all users)
                    database.execSQL("INSERT OR IGNORE INTO categories (name, icon, color, type, usageCount, isUserDeletable, isHidden, userId) VALUES ('$name', '$icon', '$color', 'EXPENSE', 0, 1, 0, NULL)")
                } catch (e: Exception) {
                    // Fallback if type is stored as integer
                    try {
                        database.execSQL("INSERT OR IGNORE INTO categories (name, icon, color, type, usageCount, isUserDeletable, isHidden, userId) VALUES ('$name', '$icon', '$color', 1, 0, 1, 0, NULL)")
                    } catch (e2: Exception) {
                        // Ignore errors
                    }
                }
            }
        }
        
        val MIGRATION_1_2 = object : androidx.room.migration.Migration(1, 2) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add currency column to accounts table with default value
                database.execSQL("ALTER TABLE accounts ADD COLUMN currency TEXT NOT NULL DEFAULT '₹'")
            }
        }
        
        val MIGRATION_2_3 = object : androidx.room.migration.Migration(2, 3) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add new fields to categories table for usage tracking
                database.execSQL("ALTER TABLE categories ADD COLUMN usageCount INTEGER NOT NULL DEFAULT 0")
                database.execSQL("ALTER TABLE categories ADD COLUMN isUserDeletable INTEGER NOT NULL DEFAULT 1")
                database.execSQL("ALTER TABLE categories ADD COLUMN isHidden INTEGER NOT NULL DEFAULT 0")
                
                // Add new fields to transactions table for auto-learning
                database.execSQL("ALTER TABLE transactions ADD COLUMN merchantName TEXT")
                database.execSQL("ALTER TABLE transactions ADD COLUMN isAutoCategorized INTEGER NOT NULL DEFAULT 0")
                
                // Create learning_rules table for silent auto-categorization
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS learning_rules (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        merchantPattern TEXT NOT NULL,
                        categoryId INTEGER NOT NULL,
                        confidenceScore REAL NOT NULL,
                        usageCount INTEGER NOT NULL,
                        createdAt TEXT NOT NULL,
                        lastUsedAt TEXT NOT NULL
                    )
                """)
                
                // Create index for fast merchant lookup
                database.execSQL("CREATE INDEX IF NOT EXISTS index_learning_rules_merchant ON learning_rules(merchantPattern)")
            }
        }
        
        val MIGRATION_3_4 = object : androidx.room.migration.Migration(3, 4) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add indices for faster queries and deduplication
                database.execSQL("CREATE INDEX IF NOT EXISTS idx_account_date ON transactions(accountId, txnDate)")
                database.execSQL("CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(txnDate)")
                database.execSQL("CREATE INDEX IF NOT EXISTS idx_dedup ON transactions(accountId, txnDate, amount, description)")
            }
        }
        
        val MIGRATION_4_5 = object : androidx.room.migration.Migration(4, 5) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add balanceAfterTxn column to transactions table for statement-based balance
                // Check if column already exists to handle partial migration scenarios
                val cursor = database.query("PRAGMA table_info(transactions)")
                var columnExists = false
                while (cursor.moveToNext()) {
                    val columnName = cursor.getString(cursor.getColumnIndex("name"))
                    if (columnName == "balanceAfterTxn") {
                        columnExists = true
                        break
                    }
                }
                cursor.close()
                
                if (!columnExists) {
                    database.execSQL("ALTER TABLE transactions ADD COLUMN balanceAfterTxn REAL")
                }
            }
        }

        val MIGRATION_5_6 = object : androidx.room.migration.Migration(5, 6) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS invoices (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        invoiceNumber TEXT NOT NULL,
                        clientName TEXT NOT NULL,
                        date INTEGER NOT NULL,
                        amount REAL NOT NULL,
                        pdfPath TEXT,
                        createdAt INTEGER NOT NULL
                    )
                """)
            }
        }

        val MIGRATION_6_7 = object : androidx.room.migration.Migration(6, 7) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Check if column exists before adding to avoid duplicate column error
                val cursor = database.query("PRAGMA table_info(invoices)")
                var hasClientAddress = false
                var hasDueDate = false
                var hasItemsJson = false
                var hasTaxRate = false
                var hasIsPaid = false

                while (cursor.moveToNext()) {
                    val name = cursor.getString(cursor.getColumnIndexOrThrow("name"))
                    when (name) {
                        "clientAddress" -> hasClientAddress = true
                        "dueDate" -> hasDueDate = true
                        "itemsJson" -> hasItemsJson = true
                        "taxRate" -> hasTaxRate = true
                        "isPaid" -> hasIsPaid = true
                    }
                }
                cursor.close()

                if (!hasClientAddress) database.execSQL("ALTER TABLE invoices ADD COLUMN clientAddress TEXT NOT NULL DEFAULT ''")
                if (!hasDueDate) database.execSQL("ALTER TABLE invoices ADD COLUMN dueDate INTEGER NOT NULL DEFAULT 0")
                if (!hasItemsJson) database.execSQL("ALTER TABLE invoices ADD COLUMN itemsJson TEXT NOT NULL DEFAULT '[]'")
                if (!hasTaxRate) database.execSQL("ALTER TABLE invoices ADD COLUMN taxRate REAL NOT NULL DEFAULT 0.0")
                if (!hasIsPaid) database.execSQL("ALTER TABLE invoices ADD COLUMN isPaid INTEGER NOT NULL DEFAULT 0")
            }
        }

        val MIGRATION_7_8 = object : androidx.room.migration.Migration(7, 8) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Insert built-in Indian categories
                insertBuiltInCategories(database)
            }
        }

        val MIGRATION_8_9 = object : androidx.room.migration.Migration(8, 9) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add userId column to all tables for data isolation between users
                
                // Check and add userId to accounts table if not exists
                var cursor = database.query("PRAGMA table_info(accounts)")
                var hasUserId = false
                while (cursor.moveToNext()) {
                    if (cursor.getString(cursor.getColumnIndex("name")) == "userId") {
                        hasUserId = true
                        break
                    }
                }
                cursor.close()
                if (!hasUserId) {
                    database.execSQL("ALTER TABLE accounts ADD COLUMN userId TEXT NOT NULL DEFAULT 'default_user'")
                }
                
                // Check and add userId to transactions table if not exists
                cursor = database.query("PRAGMA table_info(transactions)")
                hasUserId = false
                while (cursor.moveToNext()) {
                    if (cursor.getString(cursor.getColumnIndex("name")) == "userId") {
                        hasUserId = true
                        break
                    }
                }
                cursor.close()
                if (!hasUserId) {
                    database.execSQL("ALTER TABLE transactions ADD COLUMN userId TEXT NOT NULL DEFAULT 'default_user'")
                }
                
                // Check and add userId to categories table if not exists (nullable)
                cursor = database.query("PRAGMA table_info(categories)")
                hasUserId = false
                while (cursor.moveToNext()) {
                    if (cursor.getString(cursor.getColumnIndex("name")) == "userId") {
                        hasUserId = true
                        break
                    }
                }
                cursor.close()
                if (!hasUserId) {
                    database.execSQL("ALTER TABLE categories ADD COLUMN userId TEXT")
                }
                
                // Check and add userId to learning_rules table if not exists
                cursor = database.query("PRAGMA table_info(learning_rules)")
                hasUserId = false
                while (cursor.moveToNext()) {
                    if (cursor.getString(cursor.getColumnIndex("name")) == "userId") {
                        hasUserId = true
                        break
                    }
                }
                cursor.close()
                if (!hasUserId) {
                    database.execSQL("ALTER TABLE learning_rules ADD COLUMN userId TEXT NOT NULL DEFAULT 'default_user'")
                }
                
                // Check and add userId to invoices table if not exists
                cursor = database.query("PRAGMA table_info(invoices)")
                hasUserId = false
                while (cursor.moveToNext()) {
                    if (cursor.getString(cursor.getColumnIndex("name")) == "userId") {
                        hasUserId = true
                        break
                    }
                }
                cursor.close()
                if (!hasUserId) {
                    database.execSQL("ALTER TABLE invoices ADD COLUMN userId TEXT NOT NULL DEFAULT 'default_user'")
                }
                
                // Drop old indices and create new ones with userId
                database.execSQL("DROP INDEX IF EXISTS idx_account_date")
                database.execSQL("DROP INDEX IF EXISTS idx_txn_date")
                database.execSQL("CREATE INDEX IF NOT EXISTS idx_user_account_date ON transactions(userId, accountId, txnDate)")
                database.execSQL("CREATE INDEX IF NOT EXISTS idx_user_date ON transactions(userId, txnDate)")
                
                // Drop ALL old learning_rules indices and create the correct one
                database.execSQL("DROP INDEX IF EXISTS index_learning_rules_merchantPattern")
                database.execSQL("DROP INDEX IF EXISTS index_learning_rules_merchant")
                database.execSQL("DROP INDEX IF EXISTS index_learning_rules_user_merchant")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_learning_rules_userId_merchantPattern ON learning_rules(userId, merchantPattern)")
            }
        }

        val MIGRATION_9_10 = object : androidx.room.migration.Migration(9, 10) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Create user_accounts table for multi-user support with username + security question
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS user_accounts (
                        userId TEXT PRIMARY KEY NOT NULL,
                        username TEXT NOT NULL,
                        displayName TEXT NOT NULL,
                        passwordHash TEXT NOT NULL,
                        securityQuestion TEXT NOT NULL,
                        securityAnswerHash TEXT NOT NULL,
                        createdAt INTEGER NOT NULL,
                        lastLoginAt INTEGER NOT NULL,
                        isActive INTEGER NOT NULL DEFAULT 1
                    )
                """)
                // Username must be unique
                database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS index_user_accounts_username ON user_accounts(username)")
                
                // Create friends table - UUID-only, no nickname
                // Users add friends by UUID only, display name from UserAccountEntity
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS friends (
                        userId TEXT NOT NULL,
                        friendUserId TEXT NOT NULL,
                        addedAt INTEGER NOT NULL,
                        PRIMARY KEY(userId, friendUserId)
                    )
                """)
                database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS index_friends_userId_friendUserId ON friends(userId, friendUserId)")
                
                // Create split_groups table for bill splitting groups
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS split_groups (
                        groupId TEXT PRIMARY KEY NOT NULL,
                        groupName TEXT NOT NULL,
                        description TEXT,
                        createdBy TEXT NOT NULL,
                        createdAt INTEGER NOT NULL,
                        isActive INTEGER NOT NULL DEFAULT 1
                    )
                """)
                database.execSQL("CREATE INDEX IF NOT EXISTS index_split_groups_createdBy ON split_groups(createdBy)")
                
                // Create split_group_members table for group membership
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS split_group_members (
                        groupId TEXT NOT NULL,
                        userId TEXT NOT NULL,
                        addedAt INTEGER NOT NULL,
                        isActive INTEGER NOT NULL DEFAULT 1,
                        PRIMARY KEY(groupId, userId)
                    )
                """)
                database.execSQL("CREATE UNIQUE INDEX IF NOT EXISTS index_split_group_members_groupId_userId ON split_group_members(groupId, userId)")
                
                // Create split_expenses table for individual expenses
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS split_expenses (
                        expenseId TEXT PRIMARY KEY NOT NULL,
                        groupId TEXT NOT NULL,
                        description TEXT NOT NULL,
                        totalAmount REAL NOT NULL,
                        paidBy TEXT NOT NULL,
                        expenseDate INTEGER NOT NULL,
                        createdAt INTEGER NOT NULL,
                        isSettled INTEGER NOT NULL DEFAULT 0
                    )
                """)
                database.execSQL("CREATE INDEX IF NOT EXISTS index_split_expenses_groupId ON split_expenses(groupId)")
                
                // Create split_expense_shares table for individual shares
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS split_expense_shares (
                        expenseId TEXT NOT NULL,
                        userId TEXT NOT NULL,
                        shareAmount REAL NOT NULL,
                        isPaid INTEGER NOT NULL DEFAULT 0,
                        paidAt INTEGER,
                        PRIMARY KEY(expenseId, userId)
                    )
                """)
                database.execSQL("CREATE INDEX IF NOT EXISTS index_split_expense_shares_expenseId ON split_expense_shares(expenseId)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_split_expense_shares_userId ON split_expense_shares(userId)")
                
                // Ensure built-in Indian categories exist for all users
                insertBuiltInCategories(database)
            }
        }

        val MIGRATION_10_11 = object : androidx.room.migration.Migration(10, 11) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add context column to transactions table (Default: PERSONAL)
                database.execSQL("ALTER TABLE transactions ADD COLUMN context TEXT NOT NULL DEFAULT 'PERSONAL'")

                // Add context column to accounts table (Default: PERSONAL)
                database.execSQL("ALTER TABLE accounts ADD COLUMN context TEXT NOT NULL DEFAULT 'PERSONAL'")
                
                // Add isBusinessEnabled to user_accounts table (Default: 0/false)
                database.execSQL("ALTER TABLE user_accounts ADD COLUMN isBusinessEnabled INTEGER NOT NULL DEFAULT 0")
            }
        }

        val MIGRATION_11_12 = object : androidx.room.migration.Migration(11, 12) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Create savings_goals table
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS savings_goals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        userId TEXT NOT NULL,
                        name TEXT NOT NULL,
                        targetAmount REAL NOT NULL,
                        currentAmount REAL NOT NULL DEFAULT 0.0,
                        deadline INTEGER,
                        iconEmoji TEXT NOT NULL DEFAULT '🎯',
                        colorHex TEXT NOT NULL DEFAULT '#3B82F6',
                        createdAt INTEGER NOT NULL,
                        isCompleted INTEGER NOT NULL DEFAULT 0
                    )
                """)
                database.execSQL("CREATE INDEX IF NOT EXISTS index_savings_goals_userId ON savings_goals(userId)")
            }
        }

        val MIGRATION_12_13 = object : androidx.room.migration.Migration(12, 13) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Create bill_reminders table
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS bill_reminders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        userId TEXT NOT NULL,
                        name TEXT NOT NULL,
                        amount REAL NOT NULL,
                        dueDay INTEGER NOT NULL,
                        reminderDaysBefore INTEGER NOT NULL DEFAULT 3,
                        isRecurring INTEGER NOT NULL DEFAULT 1,
                        categoryId INTEGER,
                        isActive INTEGER NOT NULL DEFAULT 1,
                        lastNotifiedMonth INTEGER,
                        createdAt INTEGER NOT NULL
                    )
                """)
                database.execSQL("CREATE INDEX IF NOT EXISTS index_bill_reminders_userId ON bill_reminders(userId)")
            }
        }

        val MIGRATION_13_14 = object : androidx.room.migration.Migration(13, 14) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add monthlyBudget column to categories table
                database.execSQL("ALTER TABLE categories ADD COLUMN monthlyBudget REAL")
            }
        }

        val MIGRATION_14_15 = object : androidx.room.migration.Migration(14, 15) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Create transaction_templates table
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS transaction_templates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        userId TEXT NOT NULL,
                        name TEXT NOT NULL,
                        amount REAL NOT NULL,
                        type TEXT NOT NULL,
                        categoryId INTEGER NOT NULL,
                        description TEXT NOT NULL DEFAULT '',
                        context TEXT NOT NULL DEFAULT 'PERSONAL',
                        icon TEXT NOT NULL DEFAULT '💳',
                        createdAt INTEGER NOT NULL
                    )
                """)
                database.execSQL("CREATE INDEX IF NOT EXISTS index_transaction_templates_userId ON transaction_templates(userId)")
            }
        }

        val MIGRATION_15_16 = object : androidx.room.migration.Migration(15, 16) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add GST and TDS columns to invoices table
                database.execSQL("ALTER TABLE invoices ADD COLUMN clientGstin TEXT NOT NULL DEFAULT ''")
                database.execSQL("ALTER TABLE invoices ADD COLUMN subtotal REAL NOT NULL DEFAULT 0.0")
                database.execSQL("ALTER TABLE invoices ADD COLUMN cgst REAL NOT NULL DEFAULT 0.0")
                database.execSQL("ALTER TABLE invoices ADD COLUMN sgst REAL NOT NULL DEFAULT 0.0")
                database.execSQL("ALTER TABLE invoices ADD COLUMN igst REAL NOT NULL DEFAULT 0.0")
                database.execSQL("ALTER TABLE invoices ADD COLUMN tdsRate REAL NOT NULL DEFAULT 0.0")
                database.execSQL("ALTER TABLE invoices ADD COLUMN tdsAmount REAL NOT NULL DEFAULT 0.0")
            }
        }

        val MIGRATION_16_17 = object : androidx.room.migration.Migration(16, 17) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Create clients table
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        userId TEXT NOT NULL,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL DEFAULT '',
                        phone TEXT NOT NULL DEFAULT '',
                        address TEXT NOT NULL DEFAULT '',
                        gstin TEXT NOT NULL DEFAULT '',
                        panNumber TEXT NOT NULL DEFAULT '',
                        notes TEXT NOT NULL DEFAULT '',
                        createdAt INTEGER NOT NULL
                    )
                """)
                database.execSQL("CREATE INDEX IF NOT EXISTS index_clients_userId ON clients(userId)")
                // Add clientId to invoices
                database.execSQL("ALTER TABLE invoices ADD COLUMN clientId INTEGER")
            }
        }

        val MIGRATION_17_18 = object : androidx.room.migration.Migration(17, 18) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add streak fields to user_accounts
                database.execSQL("ALTER TABLE user_accounts ADD COLUMN currentStreak INTEGER NOT NULL DEFAULT 0")
                database.execSQL("ALTER TABLE user_accounts ADD COLUMN longestStreak INTEGER NOT NULL DEFAULT 0")
                database.execSQL("ALTER TABLE user_accounts ADD COLUMN lastLogDate INTEGER")
            }
        }
        
        val MIGRATION_18_19 = object : androidx.room.migration.Migration(18, 19) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Create debts table
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS debts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        userId TEXT NOT NULL,
                        name TEXT NOT NULL,
                        currentBalance REAL NOT NULL,
                        interestRate REAL NOT NULL,
                        minimumPayment REAL NOT NULL,
                        dueDay INTEGER NOT NULL,
                        strategy TEXT NOT NULL DEFAULT 'AVALANCHE',
                        createdAt INTEGER NOT NULL
                    )
                """)
            }
        }
        
        val MIGRATION_19_20 = object : androidx.room.migration.Migration(19, 20) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Create holdings table
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS holdings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        userId TEXT NOT NULL,
                        name TEXT NOT NULL,
                        type TEXT NOT NULL,
                        quantity REAL NOT NULL,
                        averageBuyPrice REAL NOT NULL,
                        currentMarketPrice REAL NOT NULL,
                        investedDate INTEGER NOT NULL,
                        notes TEXT NOT NULL DEFAULT ''
                    )
                """)
            }
        }
        
        val MIGRATION_20_21 = object : androidx.room.migration.Migration(20, 21) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add isTaxDeductible to categories table
                database.execSQL("ALTER TABLE categories ADD COLUMN isTaxDeductible INTEGER NOT NULL DEFAULT 0")
            }
        }
        
        val MIGRATION_21_22 = object : androidx.room.migration.Migration(21, 22) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Create recurring_patterns table for Subscription Detective feature
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS recurring_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        userId TEXT NOT NULL,
                        merchantName TEXT NOT NULL,
                        averageAmount REAL NOT NULL,
                        frequency TEXT NOT NULL,
                        intervalDays INTEGER NOT NULL,
                        occurrenceCount INTEGER NOT NULL,
                        lastTransactionDate TEXT NOT NULL,
                        nextExpectedDate TEXT NOT NULL,
                        confidenceScore REAL NOT NULL,
                        isConfirmedSubscription INTEGER NOT NULL DEFAULT 0,
                        isDismissed INTEGER NOT NULL DEFAULT 0,
                        categoryId INTEGER
                    )
                """)
                database.execSQL("CREATE INDEX IF NOT EXISTS index_recurring_patterns_userId_merchantName ON recurring_patterns(userId, merchantName)")
            }
        }
        
        val MIGRATION_22_23 = object : androidx.room.migration.Migration(22, 23) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add type column to recurring_patterns
                database.execSQL("ALTER TABLE recurring_patterns ADD COLUMN type TEXT NOT NULL DEFAULT 'EXPENSE'")
            }
        }
        val MIGRATION_23_24 = object : androidx.room.migration.Migration(23, 24) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                // Add isEssential column to categories
                database.execSQL("ALTER TABLE categories ADD COLUMN isEssential INTEGER NOT NULL DEFAULT 0")
            }
        }
        val MIGRATION_24_25 = object : androidx.room.migration.Migration(24, 25) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                try {
                    database.execSQL("ALTER TABLE transactions ADD COLUMN linkedGoalId INTEGER DEFAULT NULL")
                } catch (e: Exception) {
                    // Column might already exist
                }
            }
        }

        val MIGRATION_25_26 = object : androidx.room.migration.Migration(25, 26) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS transaction_audit_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        transactionId INTEGER NOT NULL,
                        userId TEXT NOT NULL,
                        action TEXT NOT NULL,
                        fieldName TEXT,
                        oldValue TEXT,
                        newValue TEXT,
                        timestamp TEXT NOT NULL
                    )
                """)
                database.execSQL("CREATE INDEX IF NOT EXISTS index_transaction_audit_logs_transactionId ON transaction_audit_logs(transactionId)")
                database.execSQL("CREATE INDEX IF NOT EXISTS index_transaction_audit_logs_userId ON transaction_audit_logs(userId)")
            }
        }

        val MIGRATION_26_27 = object : androidx.room.migration.Migration(26, 27) {
            override fun migrate(database: androidx.sqlite.db.SupportSQLiteDatabase) {
                database.execSQL("""
                    CREATE TABLE IF NOT EXISTS crawl_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        startUrl TEXT NOT NULL,
                        status TEXT NOT NULL,
                        startTime INTEGER NOT NULL,
                        endTime INTEGER,
                        pagesCrawled INTEGER NOT NULL,
                        outputPath TEXT NOT NULL,
                        depth INTEGER NOT NULL
                    )
                """)
            }
        }
    }
}
