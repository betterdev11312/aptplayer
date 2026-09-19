package com.aptplayer.app

import org.schabi.newpipe.extractor.NewPipe
import org.schabi.newpipe.extractor.ServiceList
import org.schabi.newpipe.extractor.search.SearchInfo
import org.schabi.newpipe.extractor.stream.StreamInfo
import org.schabi.newpipe.extractor.stream.StreamInfoItem

/**
 * Busca e resolução de áudio do YouTube.
 *
 * No desktop isso é feito pelo yt-dlp, que precisa de Python. Aqui usamos o
 * NewPipeExtractor, que faz o mesmo trabalho em Java puro e roda nativo no
 * Android.
 *
 * A mesma ideia do desktop se mantém: filtrar o que não é música, para a
 * busca não trazer vlog e gameplay.
 */
object YouTube {

    /** Uma faixa, no mesmo formato que o app desktop usa. */
    data class Track(
        val videoId: String,
        val title: String,
        val artist: String,
        val duration: Long,          // segundos
        val thumbnail: String,
    ) {
        val durationLabel: String
            get() {
                if (duration <= 0) return ""
                val m = duration / 60
                val s = duration % 60
                return if (m >= 60) "%d:%02d:%02d".format(m / 60, m % 60, s)
                else "%d:%02d".format(m, s)
            }
    }

    private var started = false

    /** Precisa rodar uma vez antes de qualquer busca. */
    fun init() {
        if (started) return
        NewPipe.init(HttpDownloader)
        started = true
    }

    // --- filtro de música (mesma lógica do core/youtube.py) ---

    private val notMusic = Regex(
        "\\b(vlog|reagindo|rea[cç][aã]o|react|gameplay|tutorial|unboxing|" +
            "podcast|entrevista|epis[oó]dio|minecraft|roblox|free ?fire|" +
            "pegadinha|desafio|challenge|story ?time|meu dia|rotina|" +
            "document[aá]rio|an[aá]lise|explicando|resumo|trailer|review|" +
            "walkthrough|no commentary|speedrun|longplay|full game|" +
            "compilation|asmr|como fazer)\\b",
        RegexOption.IGNORE_CASE,
    )

    private val musicHint = Regex(
        "\\b(official|oficial|lyric|letra|audio|clipe|ao vivo|live|remaster|" +
            "acoustic|ac[uú]stico|cover|feat|ft|remix|album)\\b",
        RegexOption.IGNORE_CASE,
    )

    private val noiseTokens = listOf(
        "(Official Video)", "(Official Music Video)", "(Official Audio)",
        "[Official Video]", "[Official Music Video]", "[Official Audio]",
        "(Lyric Video)", "(Lyrics)", "(Visualizer)", "(Audio)",
        "(HD)", "(HQ)", "(4K)", "(Clipe Oficial)", "(Video Oficial)",
    )

    private val quality = Regex(
        "\\s*[\\[(]\\s*(4k|8k|hd|hq|full ?hd|1080p?|720p?|remaster(ed)?" +
            "( \\d{4})?|official (hd )?(music )?video)\\s*[\\])]",
        RegexOption.IGNORE_CASE,
    )

    /** Quanto a entrada parece música. Negativo = provavelmente não é. */
    private fun musicScore(item: StreamInfoItem): Double {
        val title = item.name ?: ""
        val uploader = item.uploaderName ?: ""
        val seconds = item.duration

        var score = 0.0

        // música quase sempre fica entre ~1min e ~15min
        if (seconds in 75..900) score += 2
        else if (seconds > 0 && (seconds < 45 || seconds > 1800)) score -= 3

        // canais "- Topic" são gerados pelo YouTube Music
        if (uploader.endsWith("- Topic")) score += 4

        if (musicHint.containsMatchIn(title)) score += 1.5
        if (title.contains(" - ") || title.contains(" – ")) score += 1.5
        if (notMusic.containsMatchIn(title)) score -= 6

        // TÍTULO TODO GRITADO costuma ser vlog
        val shouty = Regex("[A-ZÀ-Ý]{4,}").findAll(title).count()
        if (shouty >= 3) score -= 2

        return score
    }

    private fun cleanTitle(raw: String): String {
        var out = raw
        noiseTokens.forEach { token ->
            out = out.replace(token, "", ignoreCase = true)
        }
        out = quality.replace(out, " ")
        return out.split(Regex("\\s+")).joinToString(" ").trim(' ', '-', '–', '|')
    }

    /** Separa "Artista - Música", desfazendo quando vem invertido. */
    private fun splitArtist(title: String, uploader: String): Pair<String, String> {
        listOf(" - ", " – ", " — ").forEach { sep ->
            if (title.contains(sep)) {
                val left = title.substringBefore(sep).trim()
                val right = title.substringAfter(sep).trim()
                if (left.isNotEmpty() && right.isNotEmpty()) {
                    val channel = uploader.replace(" - Topic", "").trim()
                    if (channel.isNotEmpty()) {
                        if (right.equals(channel, true)) return right to left
                        if (left.equals(channel, true)) return left to right
                    }
                    return left to right
                }
            }
        }
        return "" to title
    }

    private fun toTrack(item: StreamInfoItem): Track? {
        val url = item.url ?: return null
        val videoId = url.substringAfter("v=", "").substringBefore("&")
            .ifEmpty { url.substringAfterLast("/") }
        if (videoId.length != 11) return null

        val clean = cleanTitle(item.name ?: "")
        if (clean.isBlank()) return null

        val uploader = (item.uploaderName ?: "").replace(" - Topic", "").trim()
        val (artist, title) = splitArtist(clean, uploader)

        return Track(
            videoId = videoId,
            title = title.ifBlank { clean },
            artist = artist.ifBlank { uploader }.ifBlank { "Desconhecido" },
            duration = item.duration,
            thumbnail = "https://i.ytimg.com/vi/$videoId/mqdefault.jpg",
        )
    }

    /**
     * Busca no YouTube, mantendo só o que parece música.
     * Deve ser chamada fora da thread principal.
     */
    fun search(query: String, limit: Int = 20): List<Track> {
        init()
        if (query.isBlank()) return emptyList()

        val service = ServiceList.YouTube
        val info = SearchInfo.getInfo(
            service,
            service.searchQHFactory.fromQuery(query, listOf("videos"), ""),
        )

        val scored = info.relatedItems
            .filterIsInstance<StreamInfoItem>()
            .mapNotNull { item ->
                val track = toTrack(item) ?: return@mapNotNull null
                musicScore(item) to track
            }
            .sortedByDescending { it.first }

        val keep = scored.filter { it.first >= 1.0 }.map { it.second }
        // se nada passar o corte, devolve o que não for claramente outra coisa
        return (keep.ifEmpty {
            scored.filter { it.first > -3.0 }.map { it.second }
        }).take(limit)
    }

    /**
     * URL direta do áudio, pronta para o player.
     * Escolhe a melhor faixa só de áudio disponível.
     */
    fun audioUrl(videoId: String): String? {
        init()
        val info = StreamInfo.getInfo("https://www.youtube.com/watch?v=$videoId")
        return info.audioStreams
            .filter { !it.url.isNullOrBlank() }
            .maxByOrNull { it.averageBitrate }
            ?.url
    }

    /** Faixas relacionadas — é o que alimenta o rádio. */
    fun related(videoId: String, limit: Int = 12): List<Track> {
        init()
        val info = StreamInfo.getInfo("https://www.youtube.com/watch?v=$videoId")
        return info.relatedItems
            .filterIsInstance<StreamInfoItem>()
            .mapNotNull { toTrack(it) }
            .take(limit)
    }
}
