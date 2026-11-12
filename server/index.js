import { createApp } from './app.js';

const port = Number(process.env.PORT || 8080);
const server = createApp();
server.listen(port, process.env.HOST || '0.0.0.0', () => console.log(`Лаборатория Питона: http://localhost:${port}/site/`));
for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => server.close(() => process.exit(0)));
