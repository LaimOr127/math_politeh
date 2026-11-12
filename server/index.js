import { createApp } from './app.js';

const port = Number(process.env.PORT || 8080);
const server = createApp();
server.listen(port, process.env.HOST || '0.0.0.0', () => console.log(`Курсы: http://localhost:${port}/python/ и http://localhost:${port}/java/`));
for (const signal of ['SIGINT','SIGTERM']) process.on(signal, () => server.close(() => process.exit(0)));
