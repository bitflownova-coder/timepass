package com.bitflow.finance.di

import com.bitflow.finance.data.repository.AccountRepositoryImpl
import com.bitflow.finance.data.repository.SettingsRepositoryImpl
import com.bitflow.finance.data.repository.TransactionRepositoryImpl
import com.bitflow.finance.domain.repository.AccountRepository
import com.bitflow.finance.domain.repository.SettingsRepository
import com.bitflow.finance.domain.repository.TransactionRepository
import com.bitflow.finance.data.repository.AuthRepositoryImpl
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.data.repository.SavingsGoalRepositoryImpl
import com.bitflow.finance.domain.repository.SavingsGoalRepository
import com.bitflow.finance.data.repository.BillReminderRepositoryImpl
import com.bitflow.finance.domain.repository.BillReminderRepository
import com.bitflow.finance.data.repository.DebtRepositoryImpl
import com.bitflow.finance.domain.repository.DebtRepository
import com.bitflow.finance.data.repository.InvestmentRepositoryImpl
import com.bitflow.finance.domain.repository.InvestmentRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    abstract fun bindAccountRepository(
        accountRepositoryImpl: AccountRepositoryImpl
    ): AccountRepository

    @Binds
    abstract fun bindTransactionRepository(
        transactionRepositoryImpl: TransactionRepositoryImpl
    ): TransactionRepository

    @Binds
    abstract fun bindSettingsRepository(
        settingsRepositoryImpl: SettingsRepositoryImpl
    ): SettingsRepository

    @Binds
    abstract fun bindAuthRepository(
        authRepositoryImpl: AuthRepositoryImpl
    ): AuthRepository

    @Binds
    abstract fun bindSavingsGoalRepository(
        savingsGoalRepositoryImpl: SavingsGoalRepositoryImpl
    ): SavingsGoalRepository

    @Binds
    abstract fun bindBillReminderRepository(
        billReminderRepositoryImpl: BillReminderRepositoryImpl
    ): BillReminderRepository

    @Binds
    abstract fun bindDebtRepository(
        debtRepositoryImpl: DebtRepositoryImpl
    ): DebtRepository

    @Binds
    abstract fun bindInvestmentRepository(
        investmentRepositoryImpl: InvestmentRepositoryImpl
    ): InvestmentRepository

    @Binds
    abstract fun bindCategoryRepository(
        categoryRepositoryImpl: com.bitflow.finance.data.repository.CategoryRepositoryImpl
    ): com.bitflow.finance.domain.repository.CategoryRepository
}
