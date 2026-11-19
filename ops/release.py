import os
from pathlib import Path
import re
import subprocess
import sys



REPORTS = Path("reports/release")
REPORTS.mkdir(parents=True, exist_ok=True)


def command(*args, env=None, timeout=90, log=None):
    try:
        result = subprocess.run(args, env=env, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=timeout, check=False)
        status, output = result.returncode, result.stdout
    except subprocess.TimeoutExpired as error:
        status = 124
        output = (error.stdout or b"").decode(errors="replace") + "\nCommand timed out\n"
    if log:
        (REPORTS / log).write_text(output)
    print(output, end="", flush=True)
    return status, output.strip()


def check_release(image, revision, stage):
    print(f"=== {stage}: {revision} ===", flush=True)
    env = dict(os.environ, SERVICE_IMAGE=image)
    started, _ = command("docker", "compose", "up", "-d", "--force-recreate", "--pull", "never",
                         "--wait", "--wait-timeout", "25", env=env, timeout=40,
                         log=f"{stage}-compose.txt")
    lookup, container = command("docker", "compose", "ps", "-a", "-q", "monitor", env=env)
    checks = 1
    if lookup == 0 and container:
        checks, _ = command(sys.executable, "-m", "pytest", "-q", "checks",
                            f"--hosts=docker://{container}",
                            f"--junitxml={REPORTS / (stage + '-testinfra.xml')}",
                            log=f"{stage}-testinfra.txt")
    http, _ = command(sys.executable, "ops/verify.py", revision, "--port",
                      env["PUBLISHED_PORT"], timeout=12, log=f"{stage}-http.txt")
    logged, _ = command("docker", "compose", "logs", "--no-color", "--timestamps", "monitor",
                        env=env, log=f"{stage}-container.txt")
    return started == checks == http == logged == 0


def release(repository, revision):
    label = f"{repository}:verified"
    candidate = f"{repository}:{revision}"
    pull_status, manifest = command("docker", "pull", label, log="previous-pull.txt")
    previous = None
    if pull_status == 0:
        match = re.search(r"^Digest: (sha256:[a-f0-9]{64})$", manifest, re.M)
        if not match:
            print("Registry did not report the previous digest")
            return 1
        previous_image = f"{repository}@{match[1]}"
        inspect, previous_version = command(
            "docker", "image", "inspect", "-f",
            '{{index .Config.Labels "org.opencontainers.image.revision"}}', previous_image,
        )
        if inspect or not re.fullmatch(r"[a-f0-9]{40}", previous_version):
            return 1
        previous = previous_image, previous_version
        if not check_release(*previous, stage="previous"):
            return 1
    elif not re.search(r"manifest unknown|not found", manifest, re.I):
        return 1

    if check_release(candidate, revision, "candidate"):
        tagged, _ = command("docker", "tag", candidate, label)
        if tagged == 0:
            published, _ = command("docker", "push", label, log="promote.txt")
            if published == 0:
                print(f"Verified release published: {revision}")
                return 0

    print(f"Release rejected: {revision}")
    if previous:
        print(f"Restoring verified digest {previous[0]}")
        if check_release(*previous, stage="restored"):
            print(f"Rollback passed: /health=200 /version={previous[1]}")
        else:
            print("Rollback verification failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(release(sys.argv[1], sys.argv[2]))
