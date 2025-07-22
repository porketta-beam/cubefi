"""Debug script to find unicode error source"""

import sys
import traceback

def patch_unicode():
    """Patch unicode function to capture where it's being called"""
    
    def unicode_debug(*args, **kwargs):
        print("\n" + "="*80)
        print("UNICODE() FUNCTION CALLED!")
        print("="*80)
        print(f"Arguments: {args}")
        print(f"Keyword arguments: {kwargs}")
        print("Call stack:")
        for line in traceback.format_stack():
            print(line.strip())
        print("="*80 + "\n")
        
        # Raise error to stop execution
        raise NameError("unicode() function called - this is the source of the error!")
    
    # Add unicode to builtins to catch any calls
    import builtins
    builtins.unicode = unicode_debug
    print("Unicode debug patch applied!")

if __name__ == "__main__":
    # Apply patch before importing anything else
    patch_unicode()
    
    # Now import and test the modules that might be causing issues
    try:
        print("Testing document lifecycle service...")
        from modules.services.document_lifecycle_service import DocumentLifecycleService
        
        print("Testing metadata extractors...")
        from modules.services.metadata_extractors import DocumentMetadataService
        
        print("Testing config service...")
        from modules.services.document_config_service import DocumentConfigService
        
        print("All imports successful - unicode error not in main imports")
        
    except Exception as e:
        print(f"Error during import: {e}")
        traceback.print_exc()