def test_runtime_files(host):
    assert all(
        host.file(f"/opt/monitor/{name}").exists
        for name in ("monitor.py", "gunicorn.conf.py", "requirements.txt")
    )


def test_gunicorn_master(host):
    command = host.file("/proc/1/cmdline").content.split(b"\0")
    assert any(b"gunicorn" in arg for arg in command)
    assert b"monitor:create_app()" in command


def test_port_is_listening(host):
    port = int(host.run("printenv SERVICE_PORT").stdout.strip())
    rows = host.file("/proc/net/tcp").content_string.splitlines()[1:]
    assert any(
        int(fields[1].split(":")[1], 16) == port and fields[3] == "0A"
        for fields in map(str.split, rows)
    )


def test_effective_uid(host):
    status = host.file("/proc/1/status").content_string
    uid = next(line for line in status.splitlines() if line.startswith("Uid:"))
    assert int(uid.split()[2]) == 11020
