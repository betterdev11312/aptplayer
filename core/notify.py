"""Notificacoes do Windows.

Usa o PowerShell para disparar uma notificacao nativa (toast), sem instalar
biblioteca nenhuma. O som fica por conta da interface, que toca um arquivo
de audio - assim funciona mesmo quando o Windows silencia os toasts.

Se algo falhar aqui, o app segue normalmente: notificacao nunca pode
derrubar o player.
"""

import subprocess
import threading

APP_ID = "AptPlayer"

# XML do toast. Aspas simples no PowerShell evitam expansao de variaveis.
_SCRIPT = """
$ErrorActionPreference = 'SilentlyContinue'
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType=WindowsRuntime] | Out-Null

$xml = @'
<toast activationType="protocol" launch="aptplayer:">
  <visual>
    <binding template="ToastGeneric">
      <text>TITULO</text>
      <text>CORPO</text>
    </binding>
  </visual>
  <audio silent="true"/>
</toast>
'@

$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml($xml)
$toast = New-Object Windows.UI.Notifications.ToastNotification $doc
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('APPID').Show($toast)
"""


def _escape(text: str) -> str:
    """Protege o texto para entrar no XML do toast."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("'", "&apos;")
        .replace('"', "&quot;")
    )[:180]


def _run(title: str, body: str) -> None:
    script = (
        _SCRIPT
        .replace("TITULO", _escape(title))
        .replace("CORPO", _escape(body))
        .replace("APPID", APP_ID)
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (subprocess.SubprocessError, OSError):
        pass


def show(title: str, body: str = "") -> bool:
    """Mostra uma notificacao. Nao bloqueia: o PowerShell leva ~1s para subir."""
    if not title:
        return False
    threading.Thread(target=_run, args=(title, body), daemon=True).start()
    return True
