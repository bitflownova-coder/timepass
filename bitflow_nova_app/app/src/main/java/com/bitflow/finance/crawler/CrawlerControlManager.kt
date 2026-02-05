package com.bitflow.finance.crawler

import javax.inject.Inject
import javax.inject.Singleton
import java.util.concurrent.ConcurrentHashMap

@Singleton
class CrawlerControlManager @Inject constructor() {
    private val activeEngines = ConcurrentHashMap<Long, CrawlerEngine>()

    fun register(sessionId: Long, engine: CrawlerEngine) {
        activeEngines[sessionId] = engine
    }

    fun unregister(sessionId: Long) {
        activeEngines.remove(sessionId)
    }

    fun pause(sessionId: Long) {
        activeEngines[sessionId]?.pause()
    }

    fun resume(sessionId: Long) {
        activeEngines[sessionId]?.resume()
    }

    fun stop(sessionId: Long) {
        activeEngines[sessionId]?.stop()
    }
}
