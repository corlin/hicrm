import traceback

try:
    from src.services.vector_service import vector_service
    print("Import successful")
except Exception as e:
    print(f"Import failed: {e}")
    traceback.print_exc()
