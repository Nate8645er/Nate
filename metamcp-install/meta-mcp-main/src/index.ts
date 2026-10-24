import 'dotenv/config';
import Fastify from 'fastify';
import { randomUUID } from 'crypto';
import fastifySwagger from '@fastify/swagger';
import fastifySwaggerUi from '@fastify/swagger-ui';
import {
  jsonSchemaTransform,
  serializerCompiler,
  validatorCompiler,
} from 'fastify-type-provider-zod';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { MetaApiClient } from './client.js';
import { registerAllTools } from './tools/index.js';
import { registerRestRoutes } from './rest/proxy.js';
import { HealthResponseSchema } from './rest/schemas.js';
import { renderLandingPage, FAVICON_SVG_CONTENT } from './landing.js';
import { swaggerDarkCss } from './swagger-theme.js';

const token = process.env.META_ACCESS_TOKEN ?? '';

const API_KEY = process.env.MCP_API_KEY;
const PORT = parseInt(process.env.PORT ?? '3000', 10);

// ═══════════════════════════════════════════════════════════════════════
//  PROXY CLIENTS — scoped credentials that store a caller's Meta token
//  server-side. Lets clients that cannot send custom headers (e.g.
//  web_fetch) authenticate via ?api_key=... in the URL while the actual
//  Meta token stays in Railway secrets. See CLAUDE.md for config format.
// ═══════════════════════════════════════════════════════════════════════
interface ProxyClient {
  api_key: string;          // The caller's scoped key (send as ?api_key=...)
  meta_token: string;       // Caller's Meta Graph API token (stored server-side)
  account_id?: string;      // Default ad account for this client
  label: string;            // Human-readable label (used in logs)
  read_only?: boolean;      // If true, block all non-GET requests
  expires_at?: string;      // ISO 8601 datetime; requests after this are rejected
}

const PROXY_CLIENTS: ProxyClient[] = (() => {
  const raw = process.env.PROXY_CLIENTS;
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      console.error('PROXY_CLIENTS must be a JSON array — ignoring');
      return [];
    }
    const valid: ProxyClient[] = [];
    for (const entry of parsed) {
      if (!entry?.api_key || !entry?.meta_token || !entry?.label) {
        console.error('PROXY_CLIENTS entry missing required fields (api_key, meta_token, label) — skipping');
        continue;
      }
      valid.push(entry as ProxyClient);
    }
    return valid;
  } catch (e) {
    console.error('Failed to parse PROXY_CLIENTS env var:', e);
    return [];
  }
})();

// Track active MCP sessions with TTL
const SESSION_TTL_MS = 30 * 60 * 1000; // 30 minutes
const sessions = new Map<string, { server: McpServer; transport: StreamableHTTPServerTransport; lastSeen: number }>();

// Sweep expired sessions every 5 minutes
setInterval(() => {
  const now = Date.now();
  for (const [sid, s] of sessions) {
    if (now - s.lastSeen > SESSION_TTL_MS) {
      sessions.delete(sid);
      console.log(`Session expired: ${sid}`);
    }
  }
}, 5 * 60 * 1000).unref();

function createMcpSession(metaToken?: string, metaAccountId?: string): { server: McpServer; transport: StreamableHTTPServerTransport } {
  const resolvedToken = metaToken || token;
  if (!resolvedToken) {
    throw new Error('Missing Meta access token. Provide X-Meta-Token header or set META_ACCESS_TOKEN env var.');
  }
  const client = new MetaApiClient(resolvedToken, {
    accountId: metaAccountId ?? process.env.META_AD_ACCOUNT_ID,
    apiVersion: process.env.META_API_VERSION,
  });
  const server = new McpServer({ name: 'meta-mcp', version: '1.0.0' });
  registerAllTools(server, client);
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: () => randomUUID(),
    enableJsonResponse: false,
  });
  return { server, transport };
}

async function main() {
  const fastify = Fastify({ logger: false });

  // ═══════════════════════════════════════════════════════════════════════
  //  OPENAPI / SWAGGER
  // ═══════════════════════════════════════════════════════════════════════
  fastify.setValidatorCompiler(validatorCompiler);
  fastify.setSerializerCompiler(serializerCompiler);

  await fastify.register(fastifySwagger, {
    transform: jsonSchemaTransform,
    openapi: {
      openapi: '3.1.0',
      info: {
        title: 'Meta Ads MCP Server — REST API',
        description:
          'RESTful API for Meta (Facebook) Ads management. Proxy to the Meta Marketing API with convenience endpoints for campaigns, ad sets, ads, creatives, audiences, insights, and more.',
        version: '1.0.0',
      },
      servers: [
        { url: 'https://meta-mcp.pragmaticgrowth.com', description: 'Production' },
        { url: `http://localhost:${PORT}`, description: 'Local development' },
      ],
      components: {
        securitySchemes: {
          bearerAuth: {
            type: 'http',
            scheme: 'bearer',
            description: 'MCP API Key — required for all /mcp and /api/* endpoints. Set via MCP_API_KEY env var on the server.',
          },
          metaToken: {
            type: 'apiKey',
            in: 'header',
            name: 'X-Meta-Token',
            description: 'Meta/Facebook access token. Required for all /api/* and /mcp routes. Falls back to META_ACCESS_TOKEN env var if not provided.',
          },
        },
      },
      security: [{ bearerAuth: [] }, { metaToken: [] }],
      tags: [
        { name: 'Health', description: 'Server health check' },
        { name: 'Accounts', description: 'Ad account management' },
        { name: 'Campaigns', description: 'Campaign CRUD operations' },
        { name: 'Ad Sets', description: 'Ad set CRUD operations' },
        { name: 'Ads', description: 'Ad CRUD operations' },
        { name: 'Creatives', description: 'Ad creative management' },
        { name: 'Insights', description: 'Performance reporting and analytics' },
        { name: 'Images', description: 'Ad image management' },
        { name: 'Audiences', description: 'Custom audience management' },
        { name: 'Pixels', description: 'Facebook pixel management' },
        { name: 'Conversions', description: 'Conversions API' },
        { name: 'Proxy', description: 'Generic Meta Graph API proxy' },
        { name: 'MCP Protocol', description: 'Model Context Protocol endpoints (for AI clients)' },
      ],
    },
  });

  await fastify.register(fastifySwaggerUi, {
    routePrefix: '/docs',
    theme: {
      title: 'meta-mcp API',
      css: [{ filename: 'dark-theme.css', content: swaggerDarkCss }],
    },
  });

  // ═══════════════════════════════════════════════════════════════════════
  //  API KEY AUTH HOOK — applies to /mcp and /api/*
  //
  //  Two auth tiers:
  //  1. Master key (MCP_API_KEY)  — full access, requires X-Meta-Token header
  //  2. Proxy client (PROXY_CLIENTS) — scoped key, server injects stored
  //     Meta token automatically; respects read_only + expires_at guardrails.
  // ═══════════════════════════════════════════════════════════════════════
  fastify.addHook('onRequest', async (request, reply) => {
    // Skip auth for public pages
    if (request.url === '/' || request.url === '/health' || request.url === '/favicon.svg' || request.url.startsWith('/docs')) return;

    if (!API_KEY && PROXY_CLIENTS.length === 0) return; // No auth configured — allow all

    const authHeader = request.headers.authorization;
    const bearer = authHeader?.startsWith('Bearer ') ? authHeader.slice(7) : null;
    const queryKey = (request.query as Record<string, string>)?.api_key;
    const providedKey = bearer ?? queryKey;

    if (!providedKey) {
      reply.status(401).send({ error: 'Unauthorized — missing API key' });
      return;
    }

    // 1. Master key — full access, caller must still supply X-Meta-Token header
    if (API_KEY && providedKey === API_KEY) return;

    // 2. Proxy client — look up scoped credential and inject stored Meta token
    const client = PROXY_CLIENTS.find(c => c.api_key === providedKey);
    if (client) {
      // Expiry check
      if (client.expires_at) {
        const expiresAt = new Date(client.expires_at);
        if (!isNaN(expiresAt.getTime()) && expiresAt.getTime() < Date.now()) {
          reply.status(401).send({ error: `Unauthorized — proxy client "${client.label}" expired at ${client.expires_at}` });
          return;
        }
      }
      // Read-only gate
      if (client.read_only && request.method !== 'GET') {
        reply.status(403).send({ error: `Forbidden — proxy client "${client.label}" is read-only; only GET requests are allowed` });
        return;
      }
      // Inject stored Meta token so downstream handlers find it via the normal header path
      request.headers['x-meta-token'] = client.meta_token;
      if (client.account_id && !request.headers['x-meta-account-id']) {
        request.headers['x-meta-account-id'] = client.account_id;
      }
      const urlPath = request.url.split('?')[0];
      console.log(`[proxy-client:${client.label}] ${request.method} ${urlPath}`);
      return;
    }

    reply.status(401).send({ error: 'Unauthorized — invalid API key' });
  });

  // ═══════════════════════════════════════════════════════════════════════
  //  LANDING PAGE
  // ═══════════════════════════════════════════════════════════════════════
  fastify.get('/', { schema: { hide: true } }, async (_request, reply) => {
    reply.type('text/html').send(renderLandingPage(process.uptime()));
  });

  fastify.get('/favicon.svg', { schema: { hide: true } }, async (_request, reply) => {
    reply.type('image/svg+xml').header('cache-control', 'public, max-age=86400').send(FAVICON_SVG_CONTENT);
  });

  // ═══════════════════════════════════════════════════════════════════════
  //  HEALTH CHECK
  // ═══════════════════════════════════════════════════════════════════════
  fastify.get('/health', {
    schema: {
      tags: ['Health'],
      summary: 'Health check',
      description: 'Returns server status, tool count, available modes, and uptime.',
      response: { 200: HealthResponseSchema },
    },
  }, async () => ({
    status: 'ok' as const,
    name: 'meta-mcp',
    version: '1.0.0',
    tools: 77,
    modes: ['mcp', 'rest'],
    uptime: process.uptime(),
  }));

  // ═══════════════════════════════════════════════════════════════════════
  //  MCP PROTOCOL ENDPOINT — for Claude / MCP clients
  // ═══════════════════════════════════════════════════════════════════════

  // MCP POST — initialize or send requests
  fastify.post('/mcp', {
    schema: {
      tags: ['MCP Protocol'],
      summary: 'MCP JSON-RPC request',
      description: 'Send MCP JSON-RPC requests. Used by MCP clients (Claude, etc.) to invoke tools.',
    },
  }, async (request, reply) => {
    try {
      const sessionId = request.headers['mcp-session-id'] as string | undefined;

      if (sessionId && sessions.has(sessionId)) {
        const session = sessions.get(sessionId)!;
        session.lastSeen = Date.now();
        reply.hijack();
        await session.transport.handleRequest(request.raw, reply.raw, request.body);
      } else if (!sessionId) {
        const metaToken = request.headers['x-meta-token'] as string | undefined;
        const metaAccountId = request.headers['x-meta-account-id'] as string | undefined;
        const { server, transport } = createMcpSession(metaToken, metaAccountId);
        transport.onclose = () => {
          const sid = transport.sessionId;
          if (sid) { sessions.delete(sid); console.log(`Session closed: ${sid}`); }
        };
        await server.connect(transport);
        reply.hijack();
        await transport.handleRequest(request.raw, reply.raw, request.body);
        if (transport.sessionId) {
          sessions.set(transport.sessionId, { server, transport, lastSeen: Date.now() });
          console.log(`Session created: ${transport.sessionId}`);
        }
      } else {
        reply.status(404).send({
          jsonrpc: '2.0',
          error: { code: -32000, message: 'Session not found. Send request without mcp-session-id to create a new session.' },
          id: null,
        });
      }
    } catch (error) {
      console.error('MCP request error:', error);
      if (!reply.sent) {
        reply.status(500).send({ jsonrpc: '2.0', error: { code: -32603, message: 'Internal server error' }, id: null });
      }
    }
  });

  // MCP GET — SSE stream for notifications
  fastify.get('/mcp', {
    schema: {
      tags: ['MCP Protocol'],
      summary: 'MCP SSE stream',
      description: 'Server-Sent Events stream for MCP notifications. Requires mcp-session-id header.',
    },
  }, async (request, reply) => {
    const sessionId = request.headers['mcp-session-id'] as string | undefined;
    if (!sessionId || !sessions.has(sessionId)) {
      reply.status(404).send({ error: 'Session not found' });
      return;
    }
    const session = sessions.get(sessionId)!;
    session.lastSeen = Date.now();
    reply.hijack();
    await session.transport.handleRequest(request.raw, reply.raw);
  });

  // MCP DELETE — session termination
  fastify.delete('/mcp', {
    schema: {
      tags: ['MCP Protocol'],
      summary: 'Terminate MCP session',
      description: 'Close an active MCP session. Requires mcp-session-id header.',
    },
  }, async (request, reply) => {
    const sessionId = request.headers['mcp-session-id'] as string | undefined;
    if (!sessionId || !sessions.has(sessionId)) {
      reply.status(404).send({ error: 'Session not found' });
      return;
    }
    const { transport } = sessions.get(sessionId)!;
    sessions.delete(sessionId);
    reply.hijack();
    await transport.handleRequest(request.raw, reply.raw);
  });

  // ═══════════════════════════════════════════════════════════════════════
  //  REST API — for HTTP clients (n8n, Postman, curl, any app)
  // ═══════════════════════════════════════════════════════════════════════
  registerRestRoutes(fastify);

  // ═══════════════════════════════════════════════════════════════════════
  //  START SERVER
  // ═══════════════════════════════════════════════════════════════════════
  await fastify.listen({ port: PORT, host: '0.0.0.0' });
  console.log(`meta-mcp server running at http://0.0.0.0:${PORT}`);
  console.log(`  MCP endpoint:  http://0.0.0.0:${PORT}/mcp`);
  console.log(`  REST API:      http://0.0.0.0:${PORT}/api/v1/*`);
  console.log(`  REST proxy:    http://0.0.0.0:${PORT}/api/v1/meta/{graph_api_path}`);
  console.log(`  Health check:  http://0.0.0.0:${PORT}/health`);
  console.log(`  API docs:      http://0.0.0.0:${PORT}/docs`);
  console.log(`  API key auth:  ${API_KEY ? 'enabled' : 'disabled'}`);
  console.log(`  Meta token:    ${token ? 'from env (fallback)' : 'per-session via X-Meta-Token'}`);
  console.log(`  MCP account:   ${process.env.META_AD_ACCOUNT_ID ?? 'none (per-session via X-Meta-Account-Id)'}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
