package com.bitflow.finance.data.local

import androidx.room.TypeConverter
import com.bitflow.finance.domain.model.AccountType
import com.bitflow.finance.domain.model.CategoryType
import com.bitflow.finance.domain.model.TransactionDirection
import com.bitflow.finance.domain.model.AppMode
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

class Converters {
    @TypeConverter
    fun fromTimestamp(value: String?): LocalDateTime? {
        return value?.let { LocalDateTime.parse(it) }
    }

    @TypeConverter
    fun dateToTimestamp(date: LocalDateTime?): String? {
        return date?.toString()
    }

    @TypeConverter
    fun fromDateString(value: String?): LocalDate? {
        return value?.let { LocalDate.parse(it) }
    }

    @TypeConverter
    fun dateToString(date: LocalDate?): String? {
        return date?.toString()
    }

    @TypeConverter
    fun fromStringList(value: String?): List<String> {
        return value?.split(",")?.map { it.trim() } ?: emptyList()
    }

    @TypeConverter
    fun toStringList(list: List<String>?): String {
        return list?.joinToString(",") ?: ""
    }
    
    @TypeConverter
    fun fromAccountType(value: String) = AccountType.valueOf(value)
    @TypeConverter
    fun toAccountType(value: AccountType) = value.name

    @TypeConverter
    fun fromTransactionDirection(value: String): TransactionDirection {
        // Handle legacy DEBIT/CREDIT values
        return when (value) {
            "DEBIT" -> TransactionDirection.valueOf("EXPENSE")
            "CREDIT" -> TransactionDirection.valueOf("INCOME")
            else -> TransactionDirection.valueOf(value)
        }
    }
    
    @TypeConverter
    fun toTransactionDirection(value: TransactionDirection) = value.name

    @TypeConverter
    fun fromCategoryType(value: String) = CategoryType.valueOf(value)
    @TypeConverter
    fun toCategoryType(value: CategoryType) = value.name

    @TypeConverter
    fun fromAppMode(value: String): AppMode = try {
        AppMode.valueOf(value)
    } catch (e: Exception) {
        AppMode.PERSONAL // Default fallback
    }

    @TypeConverter
    fun toAppMode(value: AppMode) = value.name

    @TypeConverter
    fun fromAuditAction(value: String) = com.bitflow.finance.data.local.entity.AuditAction.valueOf(value)
    @TypeConverter
    fun toAuditAction(value: com.bitflow.finance.data.local.entity.AuditAction) = value.name
}
