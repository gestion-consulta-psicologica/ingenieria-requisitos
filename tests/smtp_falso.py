from __future__ import annotations

import base64
import socketserver
import threading


class _ManejadorSMTP(socketserver.StreamRequestHandler):
    def _responder(self, texto: str) -> None:
        self.wfile.write((texto + "\r\n").encode("utf-8"))

    def handle(self) -> None:
        self._responder("220 smtp-falso ESMTP")
        autenticado = not self.server.requerir_auth
        while True:
            linea = self.rfile.readline()
            if not linea:
                break
            comando = linea.decode("utf-8", errors="replace").strip()
            superior = comando.upper()
            if superior.startswith("EHLO") or superior.startswith("HELO"):
                self.wfile.write(b"250-smtp-falso\r\n")
                self.wfile.write(b"250-AUTH LOGIN PLAIN\r\n")
                self.wfile.write(b"250 OK\r\n")
            elif superior.startswith("AUTH LOGIN"):
                self._responder("334 VXNlcm5hbWU6")
                usuario = base64.b64decode(
                    self.rfile.readline().strip()
                ).decode("utf-8")
                self._responder("334 UGFzc3dvcmQ6")
                clave = base64.b64decode(
                    self.rfile.readline().strip()
                ).decode("utf-8")
                autenticado = (
                    usuario == self.server.usuario
                    and clave == self.server.clave
                )
                self._responder("235 Autenticado" if autenticado else "535 Credenciales inválidas")
            elif superior.startswith("AUTH PLAIN"):
                partes = comando.split(" ", 2)
                if len(partes) == 3:
                    datos = base64.b64decode(partes[2])
                else:
                    self._responder("334 ")
                    datos = base64.b64decode(self.rfile.readline().strip())
                _, usuario, clave = datos.split(b"\x00")
                autenticado = (
                    usuario.decode("utf-8") == self.server.usuario
                    and clave.decode("utf-8") == self.server.clave
                )
                self._responder("235 Autenticado" if autenticado else "535 Credenciales inválidas")
            elif superior.startswith("MAIL FROM"):
                self._responder("250 OK")
            elif superior.startswith("RCPT TO"):
                if self.server.rechazar_destinatario:
                    self._responder("550 Destinatario rechazado")
                else:
                    self._responder("250 OK")
            elif superior.startswith("DATA"):
                self._responder("354 Fin de datos con <CRLF>.<CRLF>")
                lineas = []
                while True:
                    linea_datos = self.rfile.readline()
                    if linea_datos in (b".\r\n", b".\n", b""):
                        break
                    lineas.append(linea_datos.decode("utf-8", errors="replace"))
                self.server.mensajes.append("".join(lineas))
                self._responder("250 Mensaje aceptado")
            elif superior.startswith("RSET") or superior.startswith("NOOP"):
                self._responder("250 OK")
            elif superior.startswith("QUIT"):
                self._responder("221 Adiós")
                break
            else:
                self._responder("250 OK")


class ServidorSMTPFalso:
    def __init__(
        self,
        *,
        usuario: str | None = None,
        clave: str | None = None,
        requerir_auth: bool = False,
        rechazar_destinatario: bool = False,
    ):
        self.mensajes: list[str] = []
        self.servidor = socketserver.ThreadingTCPServer(
            ("127.0.0.1", 0), _ManejadorSMTP
        )
        self.servidor.daemon_threads = True
        self.servidor.allow_reuse_address = True
        self.servidor.usuario = usuario
        self.servidor.clave = clave
        self.servidor.requerir_auth = requerir_auth
        self.servidor.rechazar_destinatario = rechazar_destinatario
        self.servidor.mensajes = self.mensajes
        self.hilo = threading.Thread(
            target=self.servidor.serve_forever, daemon=True
        )
        self.hilo.start()

    @property
    def puerto(self) -> int:
        return self.servidor.server_address[1]

    def cerrar(self) -> None:
        self.servidor.shutdown()
        self.servidor.server_close()
        self.hilo.join(timeout=5)
