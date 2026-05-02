package com.bitflow.finance.data.remote

import com.google.gson.JsonObject
import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import retrofit2.http.Field
import retrofit2.http.FormUrlEncoded

interface CrawlerApi {

    @FormUrlEncoded
    @POST("/crawl")
    @retrofit2.http.Headers("Accept: application/json")
    suspend fun startCrawl(
        @Field("url") url: String,
        @Field("depth") depth: Int
    ): Response<JsonObject>

    @GET("/status/{crawlId}")
    suspend fun getStatus(@Path("crawlId") crawlId: String): JsonObject

    @GET("/report/{crawlId}")
    @retrofit2.http.Headers("Accept: application/json")
    suspend fun getReport(@Path("crawlId") crawlId: String): JsonObject

    @GET("/download/{crawlId}/{type}/{filename}")
    suspend fun downloadFile(
        @Path("crawlId") crawlId: String,
        @Path("type") type: String, // content, image, document
        @Path("filename") filename: String
    ): okhttp3.ResponseBody
    
    @POST("/control/{crawlId}/{action}") // action: pause, resume, stop
    suspend fun controlCrawl(
        @Path("crawlId") crawlId: String,
        @Path("action") action: String
    ): JsonObject
    
    // We'll fetch the full list of sessions from a new endpoint if available, but for now we might rely on local DB as primary
    // Wait, the Python app has an index page with history. We should probably parse that or ask for a JSON endpoint.
    // The python code shows: @app.route('/') returns render_template.
    // We should probably ADD a Json endpoint to the Python app for history, or just track locally.
    // For now, let's stick to tracking what we start, getting updates via /status.
}
