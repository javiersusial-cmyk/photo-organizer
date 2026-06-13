"""
Silenciador de mensajes a nivel C (libjpeg, libtiff, OpenCV...).

Esos avisos ("Invalid SOS parameters for sequential JPEG",
"Incorrect count for DNGPrivateData"...) los escriben librerías en C
directamente al descriptor de error (fd 2), así que no se pueden
silenciar con el módulo `logging` de Python. Aquí se redirige fd 2
a /dev/null solo durante la apertura/decodificación de la imagen.
"""
from __future__ import annotations

import contextlib
import os
import sys


@contextlib.contextmanager
def quiet_stderr():
    """Redirige temporalmente el stderr del sistema (fd 2) a devnull."""
    try:
        sys.stderr.flush()
    except Exception:
        pass

    devnull_fd = saved_fd = None
    try:
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
        saved_fd = os.dup(2)
        os.dup2(devnull_fd, 2)
    except Exception:
        # No se pudo redirigir → seguir sin silenciar (no romper el flujo)
        if saved_fd is not None:
            try:
                os.dup2(saved_fd, 2)
            except Exception:
                pass
        for fd in (devnull_fd, saved_fd):
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass
        devnull_fd = saved_fd = None

    try:
        yield
    finally:
        if saved_fd is not None:
            try:
                os.dup2(saved_fd, 2)
            except Exception:
                pass
        for fd in (devnull_fd, saved_fd):
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass
