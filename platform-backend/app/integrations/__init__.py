"""integrations/ — MCP-Client + weitere Anbindungen (Auftrag §B.1: MCP = Kern).

- mcp_client.py : JSON-RPC-2.0-Client für MCP-Server (Plugins). Transport
  injizierbar → ohne echten Server testbar; StdioTransport spricht später einen
  echten MCP-Server-Prozess an.
"""
