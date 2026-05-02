package com.bitflow.finance.ui.screens.profile

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.domain.repository.AuthRepository
import com.bitflow.finance.domain.usecase.BehaviorAnalyzerUseCase
import com.bitflow.finance.domain.model.FinancialPersona
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class ProfileUiState(
    val fullName: String = "",
    val email: String = "",
    val photoUrl: String? = null,
    val isLoading: Boolean = false,
    val persona: FinancialPersona? = null
)

@HiltViewModel
class ProfileViewModel @Inject constructor(
    private val authRepository: AuthRepository,
    private val behaviorAnalyzerUseCase: BehaviorAnalyzerUseCase,
    private val userAccountDao: com.bitflow.finance.data.local.dao.UserAccountDao
) : ViewModel() {

    private val _uiState = MutableStateFlow(ProfileUiState())
    val uiState: StateFlow<ProfileUiState> = _uiState.asStateFlow()

    init {
        loadProfile()
    }

    private fun loadProfile() {
        viewModelScope.launch {
            authRepository.currentUserId.collect { userId ->
                if (userId != "default_user") {
                    // Combine User Data + Persona
                    combine(
                        userAccountDao.getUserFlow(userId),
                        behaviorAnalyzerUseCase(userId)
                    ) { user, persona ->
                        if (user != null) {
                            _uiState.update { 
                                it.copy(
                                    fullName = user.displayName, 
                                    email = user.username, // Using username as email/identifier
                                    photoUrl = null, // Placeholder as UserEntity doesn't have photo yet
                                    persona = persona
                                ) 
                            }
                        }
                    }.collect()
                }
            }
        }
    }

    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
        }
    }
}
