# ============================
# ✅ server.py — MCP Server (no circular imports)
# ============================
from fastmcp import FastMCP
from tools.add_registration import add_registration
from tools.view_all_registration import view_all_registration

# Create FastMCP app
app = FastMCP(name="registration-server")
os.environ["FASTMCP_STATELESS_HTTP"] = "False"

# Register tools manually
app.tool()(add_registration)
app.tool()(view_all_registration)

# ==========================================================
# ✅ Run the Server (HTTP)
# ==========================================================
if __name__ == "__main__":
    print("🚀 FastMCP Registration Server running at http://127.0.0.1:8000/mcp")
    app.run(
        transport="http",
        host="127.0.0.1",
        port=8000,
        path="/mcp",
    )

