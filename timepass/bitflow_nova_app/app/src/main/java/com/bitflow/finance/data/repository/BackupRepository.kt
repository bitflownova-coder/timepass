package com.bitflow.finance.data.repository

import android.content.Context
import android.net.Uri
import com.bitflow.finance.data.local.AppDatabase
import com.bitflow.finance.data.local.entity.*
import com.bitflow.finance.domain.model.BackupData
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.BufferedReader
import java.io.InputStreamReader
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BackupRepository @Inject constructor(
    @ApplicationContext private val context: Context,
    private val database: AppDatabase
) {
    private val gson: Gson = GsonBuilder().setPrettyPrinting().create()

    suspend fun exportData(uri: Uri): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val transactions = database.transactionDao().getAllTransactionsRaw()
            val categories = database.categoryDao().getAllCategoriesRaw()
            val goals = database.savingsGoalDao().getAllGoalsRaw()
            val bills = database.billReminderDao().getAllRemindersRaw()
            val rules = database.learningRuleDao().getAllRulesRaw()
            val patterns = database.recurringPatternDao().getAllPatternsRaw()
            val auditLogs = database.transactionAuditDao().getAllLogsRaw()

            val backupData = BackupData(
                transactions = transactions,
                categories = categories,
                savingsGoals = goals,
                billReminders = bills,
                learningRules = rules,
                recurringPatterns = patterns,
                auditLogs = auditLogs
            )

            val jsonString = gson.toJson(backupData)

            context.contentResolver.openOutputStream(uri)?.use { outputStream ->
                outputStream.write(jsonString.toByteArray())
            }
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun importData(uri: Uri): Result<Unit> = withContext(Dispatchers.IO) {
        try {
            val stringBuilder = StringBuilder()
            context.contentResolver.openInputStream(uri)?.use { inputStream ->
                BufferedReader(InputStreamReader(inputStream)).use { reader ->
                    var line: String? = reader.readLine()
                    while (line != null) {
                        stringBuilder.append(line)
                        line = reader.readLine()
                    }
                }
            }
            
            val jsonString = stringBuilder.toString()
            val backupData = gson.fromJson(jsonString, BackupData::class.java)

            // Conflict Resolution / Import Logic
            // For now, simpler approach: Upsert functionality required.
            // Since Room @Insert(onConflict = REPLACE) is easiest, we might need DAOs to support bulk inserts replacing.
            
            // database.runInTransaction {
                 // We will need upsert methods in DAOs. 
                 // If not present, we can iterate and insert.
                 
                 // Categories first (dependencies)
                 backupData.categories.forEach { database.categoryDao().insertCategoryRaw(it) }
                 
                 backupData.transactions.forEach { database.transactionDao().insertTransactionRaw(it) }
                 
                 backupData.savingsGoals.forEach { database.savingsGoalDao().insertGoalRaw(it) }
                 
                 backupData.billReminders.forEach { database.billReminderDao().insertReminderRaw(it) }
                 
                 backupData.learningRules.forEach { database.learningRuleDao().insertRuleRaw(it) }
                 
                 backupData.recurringPatterns.forEach { database.recurringPatternDao().insertPatternRaw(it) }
                 
                 backupData.auditLogs.forEach { database.transactionAuditDao().insertLog(it) }
            // }

            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
