"""Instala o APK no celular conectado.

Tenta pelo adb; se a MIUI bloquear (Xiaomi faz isso mesmo com a depuracao
ligada), copia o arquivo para a pasta Downloads do celular e explica o que
tocar na tela.

Uso:
    python tools_android_install.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APK = ROOT / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
PACOTE = "com.aptplayer.app"

CANDIDATOS = [
    Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "platform-tools" / "adb.exe",
    Path(os.environ.get("ANDROID_HOME", "")) / "platform-tools" / "adb.exe",
    Path("adb.exe"),
]


def achar_adb() -> Path | None:
    for caminho in CANDIDATOS:
        if caminho and str(caminho) != "." and caminho.exists():
            return caminho
    return None


def rodar(adb: Path, *args: str) -> subprocess.CompletedProcess:
    # MSYS_NO_PATHCONV impede o Git Bash de converter caminhos do Android
    ambiente = {**os.environ, "MSYS_NO_PATHCONV": "1"}
    return subprocess.run(
        [str(adb), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=ambiente,
    )


def main() -> None:
    adb = achar_adb()
    if not adb:
        print("adb nao encontrado. Instale o Android Studio (veja ANDROID.md).")
        sys.exit(1)

    if not APK.exists():
        print("APK nao encontrado. Compile antes:")
        print("  cd android")
        print("  gradlew.bat assembleDebug")
        sys.exit(1)

    tamanho = APK.stat().st_size / 1024 / 1024
    print(f"APK: {tamanho:.1f} MB")

    saida = rodar(adb, "devices").stdout
    conectados = [l for l in saida.splitlines()[1:] if "\tdevice" in l]
    if not conectados:
        print()
        print("Nenhum celular conectado e autorizado.")
        print("  1. Opcoes do desenvolvedor > Depuracao USB")
        print("  2. Conecte o cabo e aceite o aviso na tela do celular")
        sys.exit(1)

    print("celular:", conectados[0].split("\t")[0])
    print("instalando...")

    resultado = rodar(adb, "install", "-r", str(APK))
    texto = (resultado.stdout + resultado.stderr).strip()

    if "Success" in texto:
        print("Instalado.")
        rodar(adb, "shell", "monkey", "-p", PACOTE,
              "-c", "android.intent.category.LAUNCHER", "1")
        print("Abrindo no celular...")
        return

    if "USER_RESTRICTED" in texto:
        print("A MIUI bloqueou a instalacao por USB. Copiando para o celular...")
        destino = "/sdcard/Download/AptPlayer.apk"
        copia = rodar(adb, "push", str(APK), destino)

        if "pushed" in (copia.stdout + copia.stderr):
            print(f"Copiado para {destino}")
            print()
            print("Agora, no celular:")
            print("  1. Abra o Gerenciador de Arquivos")
            print("  2. Va em Downloads e toque em AptPlayer.apk")
            print("  3. Permita instalar de fontes desconhecidas, se pedir")
            print("  4. Espere a verificacao da MIUI (uns 10 segundos) e instale")
            print()
            print("Para instalar direto pelo cabo nas proximas vezes, ative em")
            print("Opcoes do desenvolvedor: 'Instalar via USB' e 'Depuracao USB")
            print("(Configuracoes de seguranca)'. A Xiaomi exige chip com dados")
            print("moveis ligados para liberar essas opcoes.")
        else:
            print("Nao consegui copiar:", (copia.stderr or "").strip()[:200])
        return

    if "UPDATE_INCOMPATIBLE" in texto or "SIGNATURES" in texto:
        print("Ja existe uma versao com assinatura diferente instalada.")
        print(f"Desinstale antes:  adb uninstall {PACOTE}")
        return

    print("Falhou:", texto.splitlines()[-1] if texto else "erro desconhecido")


if __name__ == "__main__":
    main()
