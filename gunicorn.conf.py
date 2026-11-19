from monitor import port_from_environment

bind = f"0.0.0.0:{port_from_environment()}"
workers = 2
timeout = 15
accesslog = "-"
errorlog = "-"
