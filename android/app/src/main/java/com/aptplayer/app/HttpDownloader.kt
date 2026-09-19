package com.aptplayer.app

import org.schabi.newpipe.extractor.downloader.Downloader
import org.schabi.newpipe.extractor.downloader.Request
import org.schabi.newpipe.extractor.downloader.Response
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL

/**
 * Cliente HTTP do NewPipeExtractor.
 *
 * A biblioteca não traz um: cada app fornece o seu. Usamos a HttpURLConnection
 * do próprio Android para não adicionar dependência (OkHttp seriam ~800 KB a
 * mais no APK, sem ganho aqui).
 */
object HttpDownloader : Downloader() {

    private const val TIMEOUT = 20_000

    // Sem um User-Agent de navegador o YouTube devolve respostas diferentes.
    private const val USER_AGENT =
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"

    override fun execute(request: Request): Response {
        val url = URL(request.url())
        val connection = url.openConnection() as HttpURLConnection

        connection.requestMethod = request.httpMethod()
        connection.connectTimeout = TIMEOUT
        connection.readTimeout = TIMEOUT
        connection.setRequestProperty("User-Agent", USER_AGENT)

        request.headers().forEach { (name, values) ->
            values.forEach { value -> connection.addRequestProperty(name, value) }
        }

        val body = request.dataToSend()
        if (body != null) {
            connection.doOutput = true
            connection.outputStream.use { it.write(body) }
        }

        return try {
            val status = connection.responseCode
            val stream = if (status >= 400) connection.errorStream
                         else connection.inputStream
            val text = stream?.bufferedReader()?.use { it.readText() } ?: ""

            Response(
                status,
                connection.responseMessage,
                connection.headerFields,
                text,
                connection.url.toString(),
            )
        } catch (exc: Exception) {
            throw IOException("Falha ao acessar ${request.url()}", exc)
        } finally {
            connection.disconnect()
        }
    }
}
