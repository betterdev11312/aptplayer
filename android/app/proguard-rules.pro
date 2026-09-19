# NewPipeExtractor usa reflexao; sem isto o release quebra.
-keep class org.schabi.newpipe.extractor.** { *; }
-keep class com.grack.nanojson.** { *; }
-dontwarn org.mozilla.javascript.**
-dontwarn org.schabi.newpipe.extractor.**

# Rhino (avalia o JavaScript que o YouTube usa para assinar as URLs)
-keep class org.mozilla.javascript.** { *; }
