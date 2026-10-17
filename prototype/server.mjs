import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('.', import.meta.url));
const types = { '.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8' };
const server = http.createServer(async (req, res) => {
  const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
  const safePath = normalize(pathname).replace(/^([.][.][/\\])+/, '').replace(/^[/\\]+/, '');
  const path = join(root, safePath || 'index.html');
  try {
    const data = await readFile(path);
    res.writeHead(200, { 'Content-Type': types[extname(path)] || 'application/octet-stream', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'strict-origin-when-cross-origin' });
    res.end(data);
  } catch {
    if (!extname(pathname)) {
      try { res.writeHead(200, { 'Content-Type': types['.html'] }); res.end(await readFile(join(root, 'index.html'))); }
      catch { res.writeHead(404); res.end('Not found'); }
    } else { res.writeHead(404); res.end('Not found'); }
  }
});
const port = Number(process.env.PORT || 4173);

if (!process.env.VERCEL) {
  server.listen(port, '127.0.0.1', () => console.log(`StudyQuest is ready at http://localhost:${port}`));
}

export default server;
