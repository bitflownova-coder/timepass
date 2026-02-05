package com.bitflow.finance.ui.screens.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.bitflow.finance.data.local.entity.UserAccountEntity
import com.bitflow.finance.domain.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()

    // Predefined security questions
    val securityQuestions = listOf(
        "What is your mother's maiden name?",
        "What was the name of your first pet?",
        "What city were you born in?",
        "What is your favorite book?",
        "What was your childhood nickname?"
    )

    fun onUsernameChange(username: String) {
        _uiState.value = _uiState.value.copy(username = username, error = null)
        
        // Check username availability during signup
        if (!_uiState.value.isLoginMode && username.length >= 3) {
            viewModelScope.launch {
                val available = authRepository.checkUsernameAvailable(username)
                _uiState.value = _uiState.value.copy(
                    usernameAvailable = if (available) true else false,
                    usernameChecked = true
                )
            }
        } else {
            _uiState.value = _uiState.value.copy(usernameChecked = false)
        }
    }

    fun onDisplayNameChange(displayName: String) {
        _uiState.value = _uiState.value.copy(displayName = displayName, error = null)
    }

    fun onPasswordChange(password: String) {
        _uiState.value = _uiState.value.copy(password = password, error = null)
    }

    fun onSecurityQuestionSelected(question: String) {
        _uiState.value = _uiState.value.copy(selectedSecurityQuestion = question, error = null)
    }

    fun onSecurityAnswerChange(answer: String) {
        _uiState.value = _uiState.value.copy(securityAnswer = answer, error = null)
    }

    fun toggleMode() {
        _uiState.value = LoginUiState(isLoginMode = !_uiState.value.isLoginMode)
    }

    fun onSubmit(onSuccess: () -> Unit) {
        val state = _uiState.value
        
        // Validation
        if (state.username.isBlank() || state.password.isBlank()) {
            _uiState.value = state.copy(error = "Please fill all required fields")
            return
        }

        if (!state.isLoginMode) {
            // Signup validation
            if (state.displayName.isBlank()) {
                _uiState.value = state.copy(error = "Please enter your display name")
                return
            }
            if (state.selectedSecurityQuestion.isBlank()) {
                _uiState.value = state.copy(error = "Please select a security question")
                return
            }
            if (state.securityAnswer.isBlank()) {
                _uiState.value = state.copy(error = "Please answer the security question")
                return
            }
        }

        viewModelScope.launch {
            _uiState.value = state.copy(isLoading = true)
            
            if (state.isLoginMode) {
                // Login flow
                authRepository.login(state.username, state.password).onSuccess { user ->
                    if (user != null) {
                        // User found - login directly
                        authRepository.loginWithAccount(user).onSuccess {
                            _uiState.value = state.copy(isLoading = false)
                            onSuccess()
                        }.onFailure {
                            _uiState.value = state.copy(isLoading = false, error = it.message)
                        }
                    } else {
                        _uiState.value = state.copy(isLoading = false, error = "Invalid username or password")
                    }
                }.onFailure {
                    _uiState.value = state.copy(isLoading = false, error = it.message)
                }
            } else {
                // Signup flow
                authRepository.signup(
                    username = state.username,
                    displayName = state.displayName,
                    password = state.password,
                    securityQuestion = state.selectedSecurityQuestion,
                    securityAnswer = state.securityAnswer
                ).onSuccess { user ->
                    // Auto-login after signup
                    authRepository.loginWithAccount(user).onSuccess {
                        _uiState.value = state.copy(isLoading = false)
                        onSuccess()
                    }.onFailure {
                        _uiState.value = state.copy(isLoading = false, error = it.message)
                    }
                }.onFailure {
                    _uiState.value = state.copy(isLoading = false, error = it.message)
                }
            }
        }
    }
}

data class LoginUiState(
    val username: String = "",
    val displayName: String = "",
    val password: String = "",
    val selectedSecurityQuestion: String = "",
    val securityAnswer: String = "",
    val isLoginMode: Boolean = true,
    val isLoading: Boolean = false,
    val error: String? = null,
    val usernameAvailable: Boolean? = null,
    val usernameChecked: Boolean = false
)
