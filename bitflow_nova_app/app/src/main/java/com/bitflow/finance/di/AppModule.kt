package com.bitflow.finance.di

import android.content.Context
import androidx.room.Room
import com.bitflow.finance.data.local.AppDatabase
import com.bitflow.finance.data.local.dao.AccountDao
import com.bitflow.finance.data.local.dao.CategoryDao
import com.bitflow.finance.data.local.dao.InvoiceDao
import com.bitflow.finance.data.local.dao.LearningRuleDao
import com.bitflow.finance.data.local.dao.TransactionDao
import com.bitflow.finance.data.local.dao.UserAccountDao
import com.bitflow.finance.data.local.dao.FriendDao
import com.bitflow.finance.data.local.dao.SplitDao
import com.bitflow.finance.data.local.dao.SavingsGoalDao
import com.bitflow.finance.data.local.dao.BillReminderDao
import com.bitflow.finance.data.local.dao.TransactionTemplateDao
import com.bitflow.finance.data.local.dao.ClientDao
import com.bitflow.finance.data.local.dao.ClientDiscussionDao
import com.bitflow.finance.data.local.dao.IncomePaymentDao
import com.bitflow.finance.data.local.dao.ExpenseRecordDao
import com.bitflow.finance.data.local.dao.DebtDao
import com.bitflow.finance.data.local.dao.HoldingDao
import com.bitflow.finance.data.local.dao.RecurringPatternDao
import com.bitflow.finance.data.local.dao.TimeEntryDao
import com.bitflow.finance.data.local.dao.QuickNoteDao
import com.bitflow.finance.data.local.dao.PasswordHistoryDao
import com.bitflow.finance.data.parser.UniversalStatementParser
import com.bitflow.finance.data.parser.StatementParser
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase {
        return Room.databaseBuilder(
            context,
            AppDatabase::class.java,
            "finance_app.db"
        )
        .addMigrations(
            AppDatabase.MIGRATION_1_2, 
            AppDatabase.MIGRATION_2_3,
            AppDatabase.MIGRATION_3_4,
            AppDatabase.MIGRATION_4_5,
            AppDatabase.MIGRATION_5_6,
            AppDatabase.MIGRATION_6_7,
            AppDatabase.MIGRATION_7_8,
            AppDatabase.MIGRATION_8_9,
            AppDatabase.MIGRATION_9_10,
            AppDatabase.MIGRATION_10_11,
            AppDatabase.MIGRATION_11_12,
            AppDatabase.MIGRATION_12_13,
            AppDatabase.MIGRATION_13_14,
            AppDatabase.MIGRATION_14_15,
            AppDatabase.MIGRATION_15_16,
            AppDatabase.MIGRATION_16_17,
            AppDatabase.MIGRATION_17_18,
            AppDatabase.MIGRATION_18_19,
            AppDatabase.MIGRATION_20_21,
            AppDatabase.MIGRATION_21_22,
            AppDatabase.MIGRATION_22_23,
            AppDatabase.MIGRATION_23_24,
            AppDatabase.MIGRATION_24_25,
            AppDatabase.MIGRATION_25_26,
            AppDatabase.MIGRATION_26_27,
            AppDatabase.MIGRATION_27_28,
            AppDatabase.MIGRATION_28_29,
            AppDatabase.MIGRATION_29_30,
            AppDatabase.MIGRATION_30_31
        )
        .addCallback(object : androidx.room.RoomDatabase.Callback() {
            override fun onCreate(db: androidx.sqlite.db.SupportSQLiteDatabase) {
                super.onCreate(db)
                // Insert built-in categories on fresh database creation
                AppDatabase.insertBuiltInCategories(db)
            }
        })
        .fallbackToDestructiveMigration()
        .build()
    }

    @Provides
    fun provideAccountDao(database: AppDatabase): AccountDao = database.accountDao()

    @Provides
    fun provideTransactionDao(database: AppDatabase): TransactionDao = database.transactionDao()

    @Provides
    fun provideCategoryDao(database: AppDatabase): CategoryDao = database.categoryDao()

    @Provides
    fun provideLearningRuleDao(database: AppDatabase): LearningRuleDao = database.learningRuleDao()

    @Provides
    fun provideInvoiceDao(database: AppDatabase): InvoiceDao = database.invoiceDao()

    @Provides
    fun provideUserAccountDao(database: AppDatabase): UserAccountDao = database.userAccountDao()

    @Provides
    fun provideFriendDao(database: AppDatabase): FriendDao = database.friendDao()

    @Provides
    fun provideSplitDao(database: AppDatabase): SplitDao = database.splitDao()

    @Provides
    fun provideSavingsGoalDao(database: AppDatabase): SavingsGoalDao = database.savingsGoalDao()

    @Provides
    fun provideBillReminderDao(database: AppDatabase): BillReminderDao = database.billReminderDao()

    @Provides
    fun provideTransactionTemplateDao(database: AppDatabase): TransactionTemplateDao = database.transactionTemplateDao()

    @Provides
    fun provideClientDao(database: AppDatabase): ClientDao = database.clientDao()

    @Provides
    fun provideClientDiscussionDao(database: AppDatabase): ClientDiscussionDao = database.clientDiscussionDao()

    @Provides
    fun provideIncomePaymentDao(database: AppDatabase): IncomePaymentDao = database.incomePaymentDao()

    @Provides
    fun provideExpenseRecordDao(database: AppDatabase): ExpenseRecordDao = database.expenseRecordDao()

    @Provides
    fun provideDebtDao(database: AppDatabase): DebtDao = database.debtDao()

    @Provides
    fun provideHoldingDao(database: AppDatabase): HoldingDao = database.holdingDao()

    @Provides
    fun provideRecurringPatternDao(database: AppDatabase): RecurringPatternDao = database.recurringPatternDao()

    @Provides
    fun provideTransactionAuditDao(database: AppDatabase): com.bitflow.finance.data.local.dao.TransactionAuditDao = database.transactionAuditDao()

    @Provides
    fun provideCrawlSessionDao(database: AppDatabase): com.bitflow.finance.data.local.dao.CrawlSessionDao = database.crawlSessionDao()

    @Provides
    fun provideTimeEntryDao(database: AppDatabase): TimeEntryDao = database.timeEntryDao()

    @Provides
    fun provideQuickNoteDao(database: AppDatabase): QuickNoteDao = database.quickNoteDao()

    @Provides
    fun providePasswordHistoryDao(database: AppDatabase): PasswordHistoryDao = database.passwordHistoryDao()

    @Provides
    fun provideStatementParser(@ApplicationContext context: Context): StatementParser {
        val parser = UniversalStatementParser()
        parser.initialize(context)
        return parser
    }

    @Provides
    @Singleton
    fun provideWorkManager(@ApplicationContext context: Context): androidx.work.WorkManager {
        return androidx.work.WorkManager.getInstance(context)
    }
}
