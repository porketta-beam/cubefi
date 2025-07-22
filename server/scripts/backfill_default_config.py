#!/usr/bin/env python3
"""
Migration script to backfill config.json and metadata.json for legacy documents

개인 프로젝트 수준으로 단순한 구조로 작성
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any

# Add server to path
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))

from modules.api.models.document_config import DocumentConfigModel
from modules.services.document_config_service import DocumentConfigService
from modules.services.metadata_extractors import DocumentMetadataService


class SimpleMigrationScript:
    """개인 프로젝트용 간단한 마이그레이션 스크립트"""
    
    def __init__(self, raw_data_root: str = "./raw_data"):
        self.raw_data_root = Path(raw_data_root)
        self.config_service = DocumentConfigService(raw_data_root)
        self.metadata_service = DocumentMetadataService()
        
    def discover_legacy_documents(self) -> List[str]:
        """레거시 문서 발견 (config.json이 없는 문서들)"""
        legacy_docs = []
        
        if not self.raw_data_root.exists():
            print("Raw data directory not found")
            return legacy_docs
            
        for doc_dir in self.raw_data_root.iterdir():
            if not doc_dir.is_dir():
                continue
                
            config_path = doc_dir / "config.json"
            metadata_path = doc_dir / "metadata.json"
            
            # 원본 파일이 있지만 config.json이나 metadata.json이 없는 경우
            original_files = list(doc_dir.glob("original.*"))
            if original_files and (not config_path.exists() or not metadata_path.exists()):
                legacy_docs.append(doc_dir.name)
                
        return legacy_docs
    
    async def migrate_single_document(self, doc_id: str) -> Dict[str, Any]:
        """단일 문서 마이그레이션"""
        doc_dir = self.raw_data_root / doc_id
        result = {
            "doc_id": doc_id,
            "config_created": False,
            "metadata_created": False,
            "errors": []
        }
        
        try:
            # 1. config.json 생성
            config_path = doc_dir / "config.json"
            if not config_path.exists():
                default_config = DocumentConfigModel()
                await self.config_service.set_config(doc_id, default_config, user_id="migration")
                result["config_created"] = True
                print(f"  + Created config.json for {doc_id}")
            
            # 2. metadata.json 생성
            metadata_path = doc_dir / "metadata.json"
            if not metadata_path.exists():
                # 원본 파일 찾기
                original_files = list(doc_dir.glob("original.*"))
                if original_files:
                    original_file = original_files[0]
                    file_extension = original_file.suffix.lower()
                    
                    # 간단한 메타데이터 생성
                    if file_extension == ".pdf":
                        content_type = "application/pdf"
                    elif file_extension == ".txt":
                        content_type = "text/plain"
                    elif file_extension in [".md", ".markdown"]:
                        content_type = "text/markdown"
                    else:
                        content_type = "application/octet-stream"
                    
                    # 실제 파일명을 알 수 없으므로 doc_id 기반으로 생성
                    filename = f"{doc_id}{file_extension}"
                    
                    metadata = await self.metadata_service.extract_metadata(
                        original_file, filename, content_type
                    )
                    
                    # metadata.json 저장
                    async with open(metadata_path, 'w', encoding='utf-8') as f:
                        await f.write(metadata.model_dump_json(indent=2))
                    
                    result["metadata_created"] = True
                    print(f"  + Created metadata.json for {doc_id}")
                else:
                    result["errors"].append("No original file found")
            
        except Exception as e:
            error_msg = f"Error migrating {doc_id}: {str(e)}"
            result["errors"].append(error_msg)
            print(f"  - {error_msg}")
            
        return result
    
    async def run_migration(self, dry_run: bool = False) -> Dict[str, Any]:
        """마이그레이션 실행"""
        print("=" * 60)
        print("RAG Lab Document Migration Script")
        print("=" * 60)
        
        if dry_run:
            print("DRY RUN MODE - No changes will be made")
            print()
        
        # 레거시 문서 발견
        legacy_docs = self.discover_legacy_documents()
        
        if not legacy_docs:
            print("No legacy documents found. Migration not needed.")
            return {
                "total_documents": 0,
                "migrated": 0,
                "failed": 0,
                "results": []
            }
        
        print(f"Found {len(legacy_docs)} legacy documents")
        print(f"Documents: {', '.join(legacy_docs)}")
        print()
        
        if dry_run:
            print("DRY RUN - Would migrate the above documents")
            return {
                "total_documents": len(legacy_docs),
                "migrated": 0,
                "failed": 0,
                "results": []
            }
        
        # 실제 마이그레이션 실행
        results = []
        migrated = 0
        failed = 0
        
        for i, doc_id in enumerate(legacy_docs, 1):
            print(f"[{i}/{len(legacy_docs)}] Migrating {doc_id}...")
            
            result = await self.migrate_single_document(doc_id)
            results.append(result)
            
            if result["errors"]:
                failed += 1
            else:
                migrated += 1
        
        print()
        print("=" * 60)
        print("Migration Complete")
        print("=" * 60)
        print(f"Total documents: {len(legacy_docs)}")
        print(f"Successfully migrated: {migrated}")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print("\nFailed documents:")
            for result in results:
                if result["errors"]:
                    print(f"  - {result['doc_id']}: {', '.join(result['errors'])}")
        
        return {
            "total_documents": len(legacy_docs),
            "migrated": migrated,
            "failed": failed,
            "results": results
        }


async def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill config.json and metadata.json for legacy documents")
    parser.add_argument("--raw-data-root", default="./raw_data", help="Raw data directory path")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated without making changes")
    
    args = parser.parse_args()
    
    # 현재 디렉토리를 server로 변경
    if not Path("raw_data").exists() and Path("server").exists():
        os.chdir("server")
    
    migration = SimpleMigrationScript(args.raw_data_root)
    result = await migration.run_migration(dry_run=args.dry_run)
    
    # 종료 코드 반환
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)