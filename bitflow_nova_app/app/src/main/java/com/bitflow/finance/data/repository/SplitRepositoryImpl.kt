package com.bitflow.finance.data.repository

import com.bitflow.finance.data.local.dao.SplitDao
import com.bitflow.finance.data.local.entity.SplitExpenseEntity
import com.bitflow.finance.data.local.entity.SplitExpenseShareEntity
import com.bitflow.finance.data.local.entity.SplitGroupEntity
import com.bitflow.finance.data.local.entity.SplitGroupMemberEntity
import com.bitflow.finance.domain.repository.SplitRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SplitRepositoryImpl @Inject constructor(
    private val splitDao: SplitDao
) : SplitRepository {
    
    override fun getUserGroups(userId: String): Flow<List<SplitGroupEntity>> {
        return splitDao.getUserGroups(userId)
    }
    
    override fun getGroupDetails(groupId: String): Flow<SplitGroupEntity?> {
        return splitDao.getGroupById(groupId)
    }
    
    override suspend fun createGroup(
        groupName: String,
        description: String,
        createdBy: String,
        memberUserIds: List<String>
    ): Result<String> {
        return try {
            if (memberUserIds.size < 2) {
                return Result.failure(Exception("Group must have at least 2 members"))
            }
            
            if (!memberUserIds.contains(createdBy)) {
                return Result.failure(Exception("Creator must be a member of the group"))
            }
            
            val groupId = UUID.randomUUID().toString()
            val group = SplitGroupEntity(
                groupId = groupId,
                groupName = groupName,
                description = description,
                createdBy = createdBy,
                createdAt = System.currentTimeMillis(),
                isActive = true
            )
            
            splitDao.insertGroup(group)
            
            // Add all members
            memberUserIds.forEach { userId ->
                val member = SplitGroupMemberEntity(
                    groupId = groupId,
                    userId = userId,
                    addedAt = System.currentTimeMillis(),
                    isActive = true
                )
                splitDao.insertGroupMember(member)
            }
            
            Result.success(groupId)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override suspend fun addMemberToGroup(groupId: String, userId: String): Result<Unit> {
        return try {
            val existingMember = splitDao.getGroupMember(groupId, userId)
            if (existingMember != null && existingMember.isActive) {
                return Result.failure(Exception("User is already a member of this group"))
            }
            
            val member = SplitGroupMemberEntity(
                groupId = groupId,
                userId = userId,
                addedAt = System.currentTimeMillis(),
                isActive = true
            )
            splitDao.insertGroupMember(member)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override suspend fun removeMemberFromGroup(groupId: String, userId: String): Result<Unit> {
        return try {
            splitDao.softDeleteGroupMember(groupId, userId)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override fun getGroupMembers(groupId: String): Flow<List<SplitGroupMemberEntity>> {
        return splitDao.getGroupMembers(groupId)
    }
    
    override fun getGroupExpenses(groupId: String): Flow<List<SplitExpenseEntity>> {
        return splitDao.getGroupExpenses(groupId)
    }
    
    override suspend fun addExpense(
        groupId: String,
        description: String,
        totalAmount: Double,
        paidBy: String,
        memberUserIds: List<String>
    ): Result<String> {
        return try {
            if (memberUserIds.isEmpty()) {
                return Result.failure(Exception("Expense must be split among at least 1 member"))
            }
            
            if (totalAmount <= 0) {
                return Result.failure(Exception("Amount must be greater than 0"))
            }
            
            val expenseId = UUID.randomUUID().toString()
            val expense = SplitExpenseEntity(
                expenseId = expenseId,
                groupId = groupId,
                description = description,
                totalAmount = totalAmount,
                paidBy = paidBy,
                expenseDate = System.currentTimeMillis(),
                createdAt = System.currentTimeMillis(),
                isSettled = false
            )
            
            splitDao.insertExpense(expense)
            
            // Calculate equal split
            val shareAmount = totalAmount / memberUserIds.size
            
            // Create shares for each member
            memberUserIds.forEach { userId ->
                val share = SplitExpenseShareEntity(
                    expenseId = expenseId,
                    userId = userId,
                    shareAmount = shareAmount,
                    isPaid = userId == paidBy, // Person who paid has already paid their share
                    paidAt = if (userId == paidBy) System.currentTimeMillis() else null
                )
                splitDao.insertExpenseShare(share)
            }
            
            Result.success(expenseId)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override suspend fun markExpenseAsSettled(expenseId: String): Result<Unit> {
        return try {
            splitDao.markExpenseAsSettled(expenseId)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override fun getExpenseShares(expenseId: String): Flow<List<SplitExpenseShareEntity>> {
        return splitDao.getExpenseShares(expenseId)
    }
    
    override suspend fun markShareAsPaid(expenseId: String, userId: String): Result<Unit> {
        return try {
            splitDao.markShareAsPaid(expenseId, userId, System.currentTimeMillis())
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    override suspend fun getGroupBalance(groupId: String, userId: String): com.bitflow.finance.data.local.dao.GroupBalance? {
        return splitDao.getGroupBalance(groupId, userId)
    }
    
    /**
     * Get user balance across all groups - FIXED to use single query instead of N+1.
     * Previously this was O(N) database queries causing UI lag.
     */
    override fun getUserBalance(userId: String): Flow<Map<String, Double>> {
        return flow {
            // Single efficient query instead of N+1 loop
            val allBalances = splitDao.getAllGroupBalancesForUser(userId)
            
            val balanceMap = allBalances.associate { groupBalance ->
                val netBalance = groupBalance.owedAmount - groupBalance.owingAmount
                groupBalance.groupId to netBalance
            }
            
            emit(balanceMap)
        }
    }
}
