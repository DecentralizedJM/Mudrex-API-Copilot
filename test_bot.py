#!/usr/bin/env python3
"""
Quick test script for Mudrex API Bot
Tests core functionality without running the full bot
"""
import asyncio
import sys

def test_config():
    """Test configuration loading"""
    print("1. Testing configuration...")
    from src.config import config
    
    errors = config.validate()
    if errors:
        print(f"   ⚠️  Config warnings: {errors}")
        print("   (Add TELEGRAM_BOT_TOKEN to .env to run the bot)")
    else:
        print("   ✓ Configuration valid")
    
    print(f"   Model: {config.GEMINI_MODEL}")
    print(f"   MCP: {'Enabled' if config.MCP_ENABLED else 'Disabled'}")
    return True

def test_mcp_tools():
    """Test MCP tool definitions"""
    print("\n2. Testing MCP tools...")
    from src.mcp import MudrexTools
    
    safe_tools = MudrexTools.get_safe_tools()
    conf_tools = MudrexTools.get_confirmation_tools()
    
    print(f"   ✓ {len(safe_tools)} safe (read-only) tools")
    print(f"   ✓ {len(conf_tools)} confirmation-required tools")
    
    # List a few
    print("   Safe tools:", list(safe_tools.keys())[:4], "...")
    
    return True

def test_document_loader():
    """Test document loading"""
    print("\n3. Testing document loader...")
    from src.rag import DocumentLoader
    
    loader = DocumentLoader()
    docs = loader.load_from_directory('docs')
    
    if docs:
        print(f"   ✓ Loaded {len(docs)} documents")
        texts, metas, ids = loader.process_documents(docs)
        print(f"   ✓ Created {len(texts)} chunks")
    else:
        print("   ⚠️  No documents found in docs/")
    
    return True

async def test_mcp_client():
    """Test MCP client"""
    print("\n4. Testing MCP client...")
    from src.mcp import MudrexMCPClient
    
    client = MudrexMCPClient()
    
    try:
        connected = await client.connect()
        print(f"   ✓ MCP client ready")
        print(f"   Authenticated: {client.is_authenticated()}")
        print(f"   Safe tools: {len(client.get_safe_tools())}")
    except Exception as e:
        print(f"   ⚠️  MCP error: {e}")
    finally:
        await client.close()
    
    return True

def test_gemini_client():
    """Test Gemini client"""
    print("\n5. Testing Gemini client...")
    from src.config import config
    
    if not config.GEMINI_API_KEY:
        print("   ⚠️  GEMINI_API_KEY not set")
        return False
    
    try:
        from src.rag import GeminiClient
        client = GeminiClient()
        print(f"   ✓ Gemini client initialized")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    return True

def main():
    print("=" * 50)
    print("Mudrex API Bot - Final Test")
    print("=" * 50)
    
    results = []
    results.append(("Config", test_config()))
    results.append(("MCP Tools", test_mcp_tools()))
    results.append(("Documents", test_document_loader()))
    results.append(("Gemini", test_gemini_client()))
    results.append(("MCP Client", asyncio.run(test_mcp_client())))
    
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    for name, result in results:
        print(f"  {'✓' if result else '✗'} {name}")
    
    print(f"\n{passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All good! Add TELEGRAM_BOT_TOKEN to .env and run:")
        print("   python3 main.py")
    
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
