import io
import pathlib
import shutil
import subprocess
import sys
import tarfile

source = pathlib.Path(__file__).resolve().parent
target = pathlib.Path(sys.argv[1]).resolve()
target.mkdir(parents=True, exist_ok=False)
archive = subprocess.check_output([
    "git", "-C", str(source.parent.parent), "archive",
    "daab18f8a3c556b54492971bcca926910d2adc28",
    "exporter/clickhouseexporter",
    "extension/bearertokenauthextension",
])
with tarfile.open(fileobj=io.BytesIO(archive)) as files:
    files.extractall(target, filter="data")
for patch in ["clickhouse-0.141.patch", "bearertokenauth-0.141.patch"]:
    subprocess.run([
        "patch", "--batch", "-p1", "-i", str(source / patch),
    ], cwd=target, check=True)
for component in ["exporter/clickhouseexporter", "extension/bearertokenauthextension"]:
    module = target / component / "go.mod"
    module.write_text("\n".join(
        line for line in module.read_text().splitlines()
        if not line.startswith("replace ")
    ) + "\n")
for name in ["builder.yaml", "generate.sh", "Dockerfile", ".dockerignore"]:
    shutil.copyfile(source / name, target / name)
