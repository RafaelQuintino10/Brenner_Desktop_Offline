# """Entrypoint do PyInstaller; define como pacote executado por módulo."""
# import os
# import sys
# from pathlib import Path

# # Sys.path contém a pasta raiz adicionada no comando de empacotamento.
# if __name__=='__main__':
#     if __package__ in (None,''):
#         sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
#     from desktop.app import run
#     run()

"""Inicializador do Barbearia Brenner Desktop."""

import os
import sys
from pathlib import Path

APP_ID = "FrontDevStudio.BarbeariaBrenner.Desktop"


def configurar_windows():
    """Define a identidade do aplicativo no Windows."""

    if os.name != "nt":
        return

    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_ID
        )
    except Exception:
        pass


if __name__ == "__main__":

    if __package__ in (None, ""):
        sys.path.insert(
            0,
            str(Path(__file__).resolve().parents[1])
        )

    configurar_windows()

    from desktop.app import run

    run()