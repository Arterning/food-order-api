module.exports = {
  apps: [{
    name: "food-order-api",
    script: "uv",
    args: "run main.py",
    cwd: process.cwd(),
    autorestart: true,
    max_restarts: 3,
    watch: false,
    max_memory_restart: "1G",
    restart_delay: 3000,
    stop_exit_codes: [0],
    time: true,
    merge_logs: true,
    log_date_format: "YYYY-MM-DD HH:mm:ss Z",
    out_file: "./logs/supervisor_out.log",
    error_file: "./logs/supervisor_err.log",
    log_file: "./logs/combined.log",
    max_size: "50M",
    retain: 10,
    env: {
      NODE_ENV: "production",
      PYTHONUNBUFFERED: "1",
      PYTHONIOENCODING: "utf-8",
      NO_COLOR: "1",
      TERM: "dumb",
      FORCE_COLOR: "0"
    }
  }]
};