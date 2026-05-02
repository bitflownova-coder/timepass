package com.bitflow.pdfconverter.core.common.mvi

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * Base ViewModel for MVI architecture.
 *
 * Usage:
 *  - [S] = UI State (what the screen renders)
 *  - [I] = Intent (user actions / events)
 *  - [E] = Side Effect (one-shot navigation, snackbar, etc.)
 */
abstract class MviViewModel<S : MviState, I : MviIntent, E : MviSideEffect>(
    initialState: S
) : ViewModel() {

    private val _state = MutableStateFlow(initialState)
    val state: StateFlow<S> = _state.asStateFlow()

    private val _sideEffects = Channel<E>(Channel.BUFFERED)
    val sideEffects = _sideEffects.receiveAsFlow()

    /**
     * Entry point for all UI-driven actions.
     */
    fun onIntent(intent: I) {
        viewModelScope.launch { handleIntent(intent) }
    }

    /**
     * Each ViewModel subclass handles its own intents here.
     */
    protected abstract suspend fun handleIntent(intent: I)

    /**
     * Update the UI state atomically.
     */
    protected fun updateState(reducer: S.() -> S) {
        _state.update(reducer)
    }

    /**
     * Fire a one-shot side effect (navigation, toast, etc.).
     */
    protected fun sendEffect(effect: E) {
        viewModelScope.launch { _sideEffects.send(effect) }
    }

    /** Convenience getter for current state inside [handleIntent]. */
    protected val currentState: S get() = _state.value
}
