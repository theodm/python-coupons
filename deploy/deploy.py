import configparser
import logging
import os

from fabric import Connection

import tarfile

logging.basicConfig(level=logging.DEBUG)

#
# Konfiguration des Skripts
#

# Name des Services
SERVICE_NAME = "python-coupons"

# Gibt an, welches Python-Executable auf dem Server soll verwendet werden soll.
PYTHON_EXECUTABLE_PATH = "python3"

# Diese Dateien aus dem Projektverzeichnis werden
# nicht auf den Ziel-Server kopiert.
files_to_ignore = [
    ".idea",
    "venv",
    ".git",
    ".gitignore",
    "tmp",
    "deploy",

    # Accounts nicht überschreiben
    "accounts.db",
    "accounts.db-shm",
    "accounts.db-wal",
]

# Liest die deploy.properties Datei ein.
secrets = configparser.ConfigParser()
secrets.read("./deploy/deploy.properties")
remote_host = secrets.get("secrets", "DEPLOY_REMOTE_HOST")
remote_user = secrets.get("secrets", "DEPLOY_REMOTE_USER")
remote_pass = secrets.get("secrets", "DEPLOY_REMOTE_PASSWORD")


# Wichtige Pfade:

# Lokaler Projekt-Pfad
local_project_path = "."
# Projekt-Pfad auf dem Ziel-Server
remote_project_path = f"/home/pi/{SERVICE_NAME}"

# Lokaler temporärer Ordner
local_temp_path = f"{local_project_path}/tmp"

# Temporärer Ordner auf dem Ziel-Server
remote_temp_path = f"/home/pi/tmp"

# Temporären Ordner lokal erstellen
os.makedirs("./tmp", exist_ok=True)


c = Connection(
    host=remote_host, user=remote_user, connect_kwargs={"password": remote_pass}
)

# Sicherstellen, dass es den Projekt-Ordner und den temporären Ordner auf dem Ziel-Server gibt.
c.run(f"mkdir -p {remote_project_path}")
c.run(f"mkdir -p {remote_temp_path}")


def create_tarfile(source_dir, output_filename, files_to_ignore):
    """
    Erstellt ein Tar-Archiv von einem Verzeichnis und ignoriert dabei bestimmte Dateien, die in files_to_ignore
    angegeben sind.

    :param source_dir: Quellverzeichnis, dessen Inhalt in das Tar-Archiv gepackt werden soll.
    :param output_filename: Ziel-Dateiname des Tar-Archivs.
    :param files_to_ignore: Liste von Dateinamen und Ordnernamen, die ignoriert werden sollen.
    :return:
    """
    with tarfile.open(output_filename, "w:gz") as tar:

        def filter_fn(tarinfo: tarfile.TarInfo):
            if os.path.basename(tarinfo.name) in files_to_ignore:
                return None

            return tarinfo

        tar.add(source_dir, arcname=os.path.basename(source_dir), filter=filter_fn)


tar_file_name = f"{SERVICE_NAME}.tar.gz"

local_tar_path = f"{local_project_path}/tmp/{tar_file_name}"
remote_tar_path = f"{remote_temp_path}/{tar_file_name}"

# Wir erstellen von unserem Projektordner ein Tar-Datei
# um diese auf dem Ziel-Server dann zu entpacken.
# Wir speichern ihn lokal in ./tmp/XXX.tar.gz ab.
create_tarfile(local_project_path, local_tar_path, files_to_ignore)

# Kopieren die Tar-Datei auf den Ziel-Server
c.put(local_tar_path, remote_tar_path)

# Tar extrahieren ins Zielverzeichnis
c.run(f"tar -xzf {remote_tar_path} -C {remote_project_path}")


def copy_and_replace_template_vars(src, target, vars_to_value: dict):
    """
    Kopiert eine Datei und ersetzt dabei die Template-Variablen durch die gegebenen Werte.

    :param src: Pfad zur Quelldatei
    :param target: Pfad zur Zieldatei
    :param vars_to_value: Dictionary mit den Variablen, die ersetzt werden sollen und deren Werten
    :return:
    """
    with open(src, "r") as f:
        content = f.read()

    for var, value in vars_to_value.items():
        content = content.replace(var, value)

    with open(target, "w", newline="\n") as f:
        f.write(content)

    return target


# Start-Skript lokal ins tmp-Verzeichnis kopieren und die Template-Variable {PROJECT_PATH} ersetzen
start_script_src = f"{local_project_path}/deploy/start.sh"
start_script_target = f"{local_temp_path}/start.sh"

start_script_target = copy_and_replace_template_vars(
    start_script_src, start_script_target, {"{PROJECT_PATH}": remote_project_path}
)

# Start-Skript auf den Ziel-Server kopieren
c.put(start_script_target, f"{remote_project_path}/deploy/start.sh")

# Start-Skript ausführbar machen
c.run(f"chmod +x {remote_project_path}/deploy/start.sh")

# Nun die benötigten Packages installieren.
c.sudo("apt-get update", warn=True)
c.sudo("apt-get install -y python3 python3-pip pipenv", warn=True)

# Das Projekt mit Pipenv installieren
c.run(
    f"cd {remote_project_path} && {PYTHON_EXECUTABLE_PATH} -m pipenv install --skip-lock"
)

# Unsere Service-Datei kopieren wir auf den Server, um
# das Projekt automatisch bei Neustart des Servers zu starten.

# Wir ersetzen die Template-Variablen in der Service-Datei
service_file_src = f"{local_project_path}/deploy/{SERVICE_NAME}.service"
service_file_target = f"{local_temp_path}/{SERVICE_NAME}.service"

service_file_target = copy_and_replace_template_vars(
    service_file_src,
    service_file_target,
    {"{PROJECT_PATH}": remote_project_path, "{PROJECT_SERVICE_NAME}": SERVICE_NAME},
)

c.put(service_file_target, f"{remote_temp_path}/{SERVICE_NAME}.service")

# Die Service-Datei kopieren wir in das Verzeichnis /etc/systemd/system/
c.sudo(f"cp {remote_temp_path}/{SERVICE_NAME}.service /etc/systemd/system/")

# chown to root and chmod 644
c.sudo(f"chown root:root /etc/systemd/system/{SERVICE_NAME}.service")
c.sudo(f"chmod 644 /etc/systemd/system/{SERVICE_NAME}.service")

# Den Service registrieren und starten.
c.sudo("systemctl daemon-reload")
c.sudo(f"systemctl enable {SERVICE_NAME}")
c.sudo(f"systemctl restart {SERVICE_NAME}")
