package com.bitflow.finance.domain.repository

import com.bitflow.finance.data.local.dao.SplitDao
import com.bitflow.finance.data.local.entity.SplitExpenseEntity
import com.bitflow.finance.data.local.entity.SplitExpenseShareEntity
import com.bitflow.finance.data.local.entity.SplitGroupEntity
import com.bitflow.finance.data.local.entity.SplitGroupMemberEntity
import kotlinx.coroutines.flow.Flow

interface SplitRepository {
    // Group Management
    fun getUserGroups(userId: String): Flow<List<SplitGroupEntity>>
    
    fun getGroupDetails(groupId: String): Flow<SplitGroupEntity?>
    
    suspend fun createGroup(
        groupName: String,
        description: String,
        createdBy: String,
        memberUserIds: List<String>
    ): Result<String> // Returns groupId
    
    suspend fun addMemberToGroup(groupId: String, userId: String): Result<Unit>
    
    suspend fun removeMemberFromGroup(groupId: String, userId: String): Result<Unit>
    
    fun getGroupMembers(groupId: String): Flow<List<SplitGroupMemberEntity>>
    
    // Expense Management
    fun getGroupExpenses(groupId: String): Flow<List<SplitExpenseEntity>>
    
    suspend fun addExpense(
        groupId: String,
        description: String,
        totalAmount: Double,
        paidBy: String,
        memberUserIds: List<String>
    ): Result<String> // Returns expenseId
    
    suspend fun markExpenseAsSettled(expenseId: String): Result<Unit>
    
    fun getExpenseShares(expenseId: String): Flow<List<SplitExpenseShareEntity>>
    
    suspend fun markShareAsPaid(expenseId: String, userId: String): Result<Unit>
    
    // Balance Calculation
    suspend fun getGroupBalance(groupId: String, userId: String): com.bitflow.finance.data.local.dao.GroupBalance?
    
    fun getUserBalance(userId: String): Flow<Map<String, Double>> // Map of groupId to balance
}
