package com.bitflow.finance.data.local.dao

import androidx.room.*
import com.bitflow.finance.data.local.entity.*
import kotlinx.coroutines.flow.Flow

@Dao
interface SplitDao {
    // Group queries
    @Query("""
        SELECT * FROM split_groups 
        WHERE groupId IN (
            SELECT groupId FROM split_group_members WHERE userId = :userId AND isActive = 1
        ) AND isActive = 1
        ORDER BY createdAt DESC
    """)
    fun getUserGroups(userId: String): Flow<List<SplitGroupEntity>>
    
    @Query("SELECT * FROM split_groups WHERE groupId = :groupId")
    fun getGroupById(groupId: String): Flow<SplitGroupEntity?>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertGroup(group: SplitGroupEntity)
    
    @Update
    suspend fun updateGroup(group: SplitGroupEntity)
    
    // Member queries
    @Query("SELECT * FROM split_group_members WHERE groupId = :groupId AND isActive = 1")
    fun getGroupMembers(groupId: String): Flow<List<SplitGroupMemberEntity>>
    
    @Query("SELECT * FROM split_group_members WHERE groupId = :groupId AND userId = :userId")
    suspend fun getGroupMember(groupId: String, userId: String): SplitGroupMemberEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertGroupMember(member: SplitGroupMemberEntity)
    
    @Query("DELETE FROM split_group_members WHERE groupId = :groupId AND userId = :userId")
    suspend fun removeGroupMember(groupId: String, userId: String)
    
    @Query("UPDATE split_group_members SET isActive = 0 WHERE groupId = :groupId AND userId = :userId")
    suspend fun softDeleteGroupMember(groupId: String, userId: String)
    
    // Expense queries
    @Query("SELECT * FROM split_expenses WHERE groupId = :groupId ORDER BY expenseDate DESC")
    fun getGroupExpenses(groupId: String): Flow<List<SplitExpenseEntity>>
    
    @Query("SELECT * FROM split_expenses WHERE expenseId = :expenseId")
    suspend fun getExpenseById(expenseId: String): SplitExpenseEntity?
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertExpense(expense: SplitExpenseEntity)
    
    @Update
    suspend fun updateExpense(expense: SplitExpenseEntity)
    
    // Share queries
    @Query("SELECT * FROM split_expense_shares WHERE expenseId = :expenseId")
    fun getExpenseShares(expenseId: String): Flow<List<SplitExpenseShareEntity>>
    
    @Query("SELECT * FROM split_expense_shares WHERE userId = :userId AND isPaid = 0")
    fun getUserUnpaidShares(userId: String): Flow<List<SplitExpenseShareEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertShare(share: SplitExpenseShareEntity)
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertExpenseShare(share: SplitExpenseShareEntity)
    
    @Query("UPDATE split_expense_shares SET isPaid = 1, paidAt = :timestamp WHERE expenseId = :expenseId AND userId = :userId")
    suspend fun markShareAsPaid(expenseId: String, userId: String, timestamp: Long)
    
    @Query("UPDATE split_expenses SET isSettled = 1 WHERE expenseId = :expenseId")
    suspend fun markExpenseAsSettled(expenseId: String)
    
    @Query("""
        SELECT 
            :userId as userId,
            SUM(CASE WHEN ses.userId = :userId AND ses.isPaid = 0 THEN ses.shareAmount ELSE 0 END) as owingAmount,
            SUM(CASE WHEN se.paidBy = :userId AND ses.userId != :userId AND ses.isPaid = 0 THEN ses.shareAmount ELSE 0 END) as owedAmount
        FROM split_expense_shares ses
        JOIN split_expenses se ON ses.expenseId = se.expenseId
        WHERE se.groupId = :groupId
    """)
    suspend fun getGroupBalance(groupId: String, userId: String): GroupBalance?
    
    /**
     * Efficiently fetch all group balances for a user in a single query.
     * Prevents N+1 query problem when loading the dashboard.
     */
    @Query("""
        SELECT 
            sg.groupId,
            sg.groupName,
            COALESCE(SUM(CASE WHEN ses.userId = :userId AND ses.isPaid = 0 THEN ses.shareAmount ELSE 0 END), 0) as owingAmount,
            COALESCE(SUM(CASE WHEN se.paidBy = :userId AND ses.userId != :userId AND ses.isPaid = 0 THEN ses.shareAmount ELSE 0 END), 0) as owedAmount
        FROM split_groups sg
        LEFT JOIN split_expenses se ON sg.groupId = se.groupId
        LEFT JOIN split_expense_shares ses ON se.expenseId = ses.expenseId
        WHERE sg.isActive = 1
          AND sg.groupId IN (SELECT groupId FROM split_group_members WHERE userId = :userId AND isActive = 1)
        GROUP BY sg.groupId
    """)
    suspend fun getAllGroupBalancesForUser(userId: String): List<GroupBalanceWithName>
}

data class GroupBalance(
    val userId: String,
    val owingAmount: Double,  // Amount user owes to others
    val owedAmount: Double    // Amount others owe to user
)

data class GroupBalanceWithName(
    val groupId: String,
    val groupName: String,
    val owingAmount: Double,
    val owedAmount: Double
)
