package com.bitflow.pdfconverter.feature.editor.engine

/**
 * Generic command-pattern undo/redo stack.
 *
 * Each [Command] encapsulates a reversible operation. Call [execute] to apply and push,
 * [undo] to reverse, [redo] to reapply.
 */
interface Command {
    fun execute()
    fun undo()
}

class UndoRedoStack(private val maxSize: Int = 50) {

    private val undoStack = ArrayDeque<Command>()
    private val redoStack = ArrayDeque<Command>()

    val canUndo: Boolean get() = undoStack.isNotEmpty()
    val canRedo: Boolean get() = redoStack.isNotEmpty()

    /** Executes the [command], pushes it to the undo stack, and clears redo history. */
    fun execute(command: Command) {
        command.execute()
        undoStack.addLast(command)
        redoStack.clear()
        if (undoStack.size > maxSize) undoStack.removeFirst()
    }

    /** Undoes the most recent command and moves it to the redo stack. */
    fun undo() {
        if (!canUndo) return
        val command = undoStack.removeLast()
        command.undo()
        redoStack.addLast(command)
    }

    /** Reapplies the most recently undone command. */
    fun redo() {
        if (!canRedo) return
        val command = redoStack.removeLast()
        command.execute()
        undoStack.addLast(command)
    }

    fun clear() {
        undoStack.clear()
        redoStack.clear()
    }
}
