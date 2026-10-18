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
    "7bf85220afc6a650e6a298790d244f3f83f581e6",
    "exporter/clickhouseexporter",
])
with tarfile.open(fileobj=io.BytesIO(archive)) as files:
    files.extractall(target, filter="data")
subprocess.run([
    "patch", "--batch", "-p1", "-i", str(source / "clickhouse-0.136.patch"),
], cwd=target, check=True)
module = target / "exporter/clickhouseexporter/go.mod"
module.write_text("\n".join(
    line for line in module.read_text().splitlines()
    if not line.startswith("replace ")
) + "\n")
for name in ["builder.yaml", "Dockerfile"]:
    shutil.copyfile(source / name, target / name)
