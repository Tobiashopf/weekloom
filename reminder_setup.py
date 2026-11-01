"""Manage this database's interactive Windows scheduled task without PowerShell."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timedelta
import re
import tempfile
import xml.etree.ElementTree as ET


def task_name(data):
    digest = hashlib.sha256(str(Path(data).resolve()).lower().encode("utf-8")).hexdigest()[:12]
    return "PlanoLocal-Reminders-" + digest


def command(mode, data):
    name = task_name(data)
    if mode == "Status":
        return ["schtasks.exe", "/Query", "/TN", name, "/FO", "LIST"]
    if mode == "Remove":
        return ["schtasks.exe", "/Delete", "/TN", name, "/F"]
    raise ValueError("Unsupported mode")


def task_xml(data, python, sid):
    """Use XML registration so long installation paths do not hit /TR's length limit."""
    data = Path(data).resolve()
    if not data.is_file():
        raise ValueError("Abra o aplicativo antes de ativar os lembretes.")
    executable = Path(python).with_name("pythonw.exe").resolve()
    if not executable.is_file():
        raise ValueError("A instalação do Python precisa incluir pythonw.exe.")
    worker = Path(__file__).resolve().with_name("notifications.py")
    root = ET.Element("Task", version="1.2", xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task")
    info = ET.SubElement(root, "RegistrationInfo")
    ET.SubElement(info, "Description").text = "Weekloom personal task reminders; checks every five minutes while the user is signed in."
    triggers = ET.SubElement(root, "Triggers")
    trigger = ET.SubElement(triggers, "TimeTrigger")
    repetition = ET.SubElement(trigger, "Repetition")
    ET.SubElement(repetition, "Interval").text = "PT5M"
    ET.SubElement(repetition, "StopAtDurationEnd").text = "false"
    ET.SubElement(trigger, "StartBoundary").text = (datetime.now() + timedelta(minutes=1)).replace(microsecond=0).isoformat()
    ET.SubElement(trigger, "Enabled").text = "true"
    principals = ET.SubElement(root, "Principals")
    principal = ET.SubElement(principals, "Principal", id="CurrentUser")
    ET.SubElement(principal, "UserId").text = sid
    ET.SubElement(principal, "LogonType").text = "InteractiveToken"
    ET.SubElement(principal, "RunLevel").text = "LeastPrivilege"
    settings = ET.SubElement(root, "Settings")
    for key, value in (("MultipleInstancesPolicy", "IgnoreNew"), ("DisallowStartIfOnBatteries", "false"),
                       ("StopIfGoingOnBatteries", "false"), ("StartWhenAvailable", "true"),
                       ("ExecutionTimeLimit", "PT2M"), ("Enabled", "true")):
        ET.SubElement(settings, key).text = value
    actions = ET.SubElement(root, "Actions", Context="CurrentUser")
    action = ET.SubElement(actions, "Exec")
    ET.SubElement(action, "Command").text = str(executable)
    ET.SubElement(action, "Arguments").text = subprocess.list2cmdline([str(worker), "--data", str(data)])
    return ET.tostring(root, encoding="utf-16", xml_declaration=True)


def manage(mode, data):
    if sys.platform != "win32":
        raise RuntimeError("Esta integração requer Windows.")
    flags = subprocess.CREATE_NO_WINDOW
    if mode == "Install":
        identity = subprocess.run(["whoami.exe", "/user", "/fo", "csv", "/nh"], capture_output=True, timeout=10, creationflags=flags)
        sid = re.search(rb"S-1-\d+(?:-\d+)+", identity.stdout)
        if identity.returncode or not sid:
            raise RuntimeError("Não foi possível identificar a sessão do Windows.")
        content = task_xml(data, sys.executable, sid.group().decode("ascii"))
        with tempfile.TemporaryDirectory(prefix="plano-local-") as temp:
            definition = Path(temp) / "reminders.xml"
            definition.write_bytes(content)
            result = subprocess.run(["schtasks.exe", "/Create", "/TN", task_name(data), "/XML", str(definition), "/F"], capture_output=True, timeout=30, creationflags=flags)
    else:
        result = subprocess.run(command(mode, data), capture_output=True, timeout=30, creationflags=flags)
    output = (result.stdout + result.stderr).decode("oem", errors="replace").strip()
    if result.returncode:
        raise RuntimeError(output or "O Windows não permitiu acessar o agendamento.")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("Install", "Remove", "Status"))
    parser.add_argument("--data", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(manage(args.mode, args.data))
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
