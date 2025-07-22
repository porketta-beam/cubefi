#!/usr/bin/env python3
"""
Simple performance test for RAG Lab
개인 프로젝트용 간단한 성능 테스트
"""

import asyncio
import time
import tempfile
import io
from pathlib import Path
from typing import List, Dict, Any

# FastAPI 테스트 클라이언트
from fastapi.testclient import TestClient

# 서버 임포트
import sys
server_root = Path(__file__).parent.parent
sys.path.insert(0, str(server_root))

from main import app


class SimplePerformanceTest:
    """간단한 성능 테스트"""
    
    def __init__(self):
        self.client = TestClient(app)
        self.results = []
    
    def create_sample_files(self, count: int = 5) -> List[Dict[str, Any]]:
        """샘플 파일 생성"""
        files = []
        
        # PDF 샘플
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n'
        
        for i in range(count):
            if i % 2 == 0:
                # PDF 파일
                files.append({
                    "filename": f"test_document_{i}.pdf",
                    "content": pdf_content + b'\n' + b'a' * (1000 * (i + 1)),  # 크기 다양화
                    "content_type": "application/pdf"
                })
            else:
                # 텍스트 파일
                text_content = f"Test document {i}\n" + "Sample content. " * (100 * (i + 1))
                files.append({
                    "filename": f"test_document_{i}.txt",
                    "content": text_content.encode(),
                    "content_type": "text/plain"
                })
        
        return files
    
    def test_upload_performance(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """업로드 성능 테스트"""
        print("Testing upload performance...")
        
        doc_ids = []
        upload_times = []
        
        for i, file_data in enumerate(files):
            print(f"  Uploading file {i+1}/{len(files)}: {file_data['filename']}")
            
            start_time = time.time()
            
            response = self.client.post("/documents/upload", files={
                "file": (
                    file_data["filename"],
                    io.BytesIO(file_data["content"]),
                    file_data["content_type"]
                )
            })
            
            end_time = time.time()
            upload_time = end_time - start_time
            upload_times.append(upload_time)
            
            if response.status_code == 200:
                doc_ids.append(response.json()["doc_id"])
                print(f"    ✓ Uploaded in {upload_time:.3f}s")
            else:
                print(f"    ✗ Upload failed: {response.status_code}")
        
        avg_upload_time = sum(upload_times) / len(upload_times) if upload_times else 0
        max_upload_time = max(upload_times) if upload_times else 0
        
        return {
            "test": "upload",
            "files_uploaded": len(doc_ids),
            "doc_ids": doc_ids,
            "avg_time": avg_upload_time,
            "max_time": max_upload_time,
            "upload_times": upload_times
        }
    
    def test_config_performance(self, doc_ids: List[str]) -> Dict[str, Any]:
        """설정 조회/업데이트 성능 테스트"""
        print("Testing config performance...")
        
        get_times = []
        update_times = []
        
        for i, doc_id in enumerate(doc_ids):
            print(f"  Testing config for document {i+1}/{len(doc_ids)}")
            
            # GET 성능 테스트
            start_time = time.time()
            response = self.client.get(f"/documents/{doc_id}/config")
            get_time = time.time() - start_time
            get_times.append(get_time)
            
            if response.status_code != 200:
                print(f"    ✗ Config GET failed: {response.status_code}")
                continue
            
            # PUT 성능 테스트
            new_config = {
                "chunk": {
                    "chunk_size": 256 + (i * 64),  # 다양한 크기
                    "chunk_overlap": 20 + (i * 5)
                }
            }
            
            start_time = time.time()
            response = self.client.put(f"/documents/{doc_id}/config", json=new_config)
            update_time = time.time() - start_time
            update_times.append(update_time)
            
            if response.status_code == 200:
                print(f"    ✓ Config GET: {get_time:.3f}s, PUT: {update_time:.3f}s")
            else:
                print(f"    ✗ Config PUT failed: {response.status_code}")
        
        return {
            "test": "config",
            "documents_tested": len(doc_ids),
            "avg_get_time": sum(get_times) / len(get_times) if get_times else 0,
            "avg_update_time": sum(update_times) / len(update_times) if update_times else 0,
            "max_get_time": max(get_times) if get_times else 0,
            "max_update_time": max(update_times) if update_times else 0
        }
    
    def test_sync_performance(self, doc_ids: List[str]) -> Dict[str, Any]:
        """동기화 성능 테스트"""
        print("Testing sync performance...")
        
        # 단일 문서 동기화
        single_sync_times = []
        for i, doc_id in enumerate(doc_ids[:3]):  # 처음 3개만 테스트
            print(f"  Single sync {i+1}/3: {doc_id}")
            
            start_time = time.time()
            response = self.client.get(f"/documents/sync?doc_id={doc_id}")
            sync_time = time.time() - start_time
            single_sync_times.append(sync_time)
            
            if response.status_code == 200:
                print(f"    ✓ Synced in {sync_time:.3f}s")
            else:
                print(f"    ✗ Sync failed: {response.status_code}")
        
        # 전체 동기화
        print("  Testing bulk sync...")
        start_time = time.time()
        response = self.client.get("/documents/sync")
        bulk_sync_time = time.time() - start_time
        
        bulk_success = response.status_code == 200
        if bulk_success:
            print(f"    ✓ Bulk sync completed in {bulk_sync_time:.3f}s")
        else:
            print(f"    ✗ Bulk sync failed: {response.status_code}")
        
        return {
            "test": "sync",
            "single_sync_times": single_sync_times,
            "avg_single_sync": sum(single_sync_times) / len(single_sync_times) if single_sync_times else 0,
            "bulk_sync_time": bulk_sync_time,
            "bulk_sync_success": bulk_success
        }
    
    def test_delete_performance(self, doc_ids: List[str]) -> Dict[str, Any]:
        """삭제 성능 테스트"""
        print("Testing delete performance...")
        
        delete_times = []
        successful_deletes = 0
        
        for i, doc_id in enumerate(doc_ids):
            print(f"  Deleting document {i+1}/{len(doc_ids)}")
            
            start_time = time.time()
            response = self.client.delete(f"/documents/{doc_id}")
            delete_time = time.time() - start_time
            delete_times.append(delete_time)
            
            if response.status_code == 204:
                successful_deletes += 1
                print(f"    ✓ Deleted in {delete_time:.3f}s")
            else:
                print(f"    ✗ Delete failed: {response.status_code}")
        
        return {
            "test": "delete",
            "documents_deleted": successful_deletes,
            "total_documents": len(doc_ids),
            "avg_delete_time": sum(delete_times) / len(delete_times) if delete_times else 0,
            "max_delete_time": max(delete_times) if delete_times else 0
        }
    
    def run_performance_tests(self, num_files: int = 5) -> Dict[str, Any]:
        """성능 테스트 실행"""
        print("=" * 60)
        print(f"RAG Lab Performance Test ({num_files} files)")
        print("=" * 60)
        
        overall_start = time.time()
        
        # 1. 샘플 파일 생성
        print("\n1. Creating sample files...")
        files = self.create_sample_files(num_files)
        print(f"   Created {len(files)} sample files")
        
        # 2. 업로드 성능 테스트
        print("\n2. Upload Performance Test")
        upload_result = self.test_upload_performance(files)
        self.results.append(upload_result)
        
        if not upload_result["doc_ids"]:
            print("   ✗ No documents uploaded successfully, skipping other tests")
            return {"error": "Upload test failed"}
        
        # 3. 설정 성능 테스트
        print("\n3. Config Performance Test")
        config_result = self.test_config_performance(upload_result["doc_ids"])
        self.results.append(config_result)
        
        # 4. 동기화 성능 테스트
        print("\n4. Sync Performance Test")
        sync_result = self.test_sync_performance(upload_result["doc_ids"])
        self.results.append(sync_result)
        
        # 5. 삭제 성능 테스트
        print("\n5. Delete Performance Test")
        delete_result = self.test_delete_performance(upload_result["doc_ids"])
        self.results.append(delete_result)
        
        overall_time = time.time() - overall_start
        
        # 결과 요약
        summary = self.generate_summary(overall_time)
        
        return {
            "summary": summary,
            "detailed_results": self.results,
            "total_time": overall_time
        }
    
    def generate_summary(self, total_time: float) -> Dict[str, Any]:
        """결과 요약 생성"""
        print("\n" + "=" * 60)
        print("Performance Test Summary")
        print("=" * 60)
        
        summary = {
            "total_test_time": total_time,
            "tests_completed": len(self.results)
        }
        
        for result in self.results:
            test_name = result["test"]
            print(f"\n{test_name.upper()} Test:")
            
            if test_name == "upload":
                print(f"  Files uploaded: {result['files_uploaded']}")
                print(f"  Average time: {result['avg_time']:.3f}s")
                print(f"  Max time: {result['max_time']:.3f}s")
                summary["upload"] = {
                    "files": result['files_uploaded'],
                    "avg_time": result['avg_time']
                }
            
            elif test_name == "config":
                print(f"  Documents tested: {result['documents_tested']}")
                print(f"  Avg GET time: {result['avg_get_time']:.3f}s")
                print(f"  Avg PUT time: {result['avg_update_time']:.3f}s")
                summary["config"] = {
                    "avg_get": result['avg_get_time'],
                    "avg_put": result['avg_update_time']
                }
            
            elif test_name == "sync":
                print(f"  Avg single sync: {result['avg_single_sync']:.3f}s")
                print(f"  Bulk sync time: {result['bulk_sync_time']:.3f}s")
                summary["sync"] = {
                    "single": result['avg_single_sync'],
                    "bulk": result['bulk_sync_time']
                }
            
            elif test_name == "delete":
                print(f"  Documents deleted: {result['documents_deleted']}/{result['total_documents']}")
                print(f"  Avg delete time: {result['avg_delete_time']:.3f}s")
                summary["delete"] = {
                    "success_rate": result['documents_deleted'] / result['total_documents'],
                    "avg_time": result['avg_delete_time']
                }
        
        print(f"\nTotal test time: {total_time:.2f}s")
        
        # 성능 평가
        self.evaluate_performance(summary)
        
        return summary
    
    def evaluate_performance(self, summary: Dict[str, Any]):
        """성능 평가 및 권장사항"""
        print("\n" + "-" * 40)
        print("Performance Evaluation:")
        
        issues = []
        recommendations = []
        
        # 업로드 성능 평가
        if "upload" in summary and summary["upload"]["avg_time"] > 2.0:
            issues.append("Upload times are high (>2s average)")
            recommendations.append("Consider optimizing file processing or using background tasks")
        
        # 설정 성능 평가
        if "config" in summary:
            if summary["config"]["avg_get"] > 0.1:
                issues.append("Config GET times are high (>0.1s)")
            if summary["config"]["avg_put"] > 0.5:
                issues.append("Config PUT times are high (>0.5s)")
                recommendations.append("Consider caching config data")
        
        # 동기화 성능 평가
        if "sync" in summary and summary["sync"]["bulk"] > 10.0:
            issues.append("Bulk sync time is high (>10s)")
            recommendations.append("Consider implementing parallel processing")
        
        if issues:
            print("  Issues found:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  ✓ No significant performance issues detected")
        
        if recommendations:
            print("  Recommendations:")
            for rec in recommendations:
                print(f"    - {rec}")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run performance tests for RAG Lab")
    parser.add_argument("--files", type=int, default=5, help="Number of test files to create")
    parser.add_argument("--output", help="Output file for results (JSON)")
    
    args = parser.parse_args()
    
    # 현재 디렉토리를 server로 변경
    if not Path("raw_data").exists() and Path("server").exists():
        import os
        os.chdir("server")
    
    # 성능 테스트 실행
    tester = SimplePerformanceTest()
    results = tester.run_performance_tests(args.files)
    
    # 결과 저장
    if args.output:
        import json
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")


if __name__ == "__main__":
    main()