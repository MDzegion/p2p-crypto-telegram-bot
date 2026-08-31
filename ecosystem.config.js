module.exports = {
  apps: [
    {
      name: 'gopay-gateway',
      cwd: './gopay-gateway',
      script: 'server.js',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      env: {
        GOPAY_PORT: 3005,
        NODE_ENV: 'production'
      }
    },
    {
      name: 'p2p-telegram-bot',
      cwd: './',
      script: 'main.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M'
    }
  ]
};
