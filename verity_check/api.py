"""
FastAPI service for triggering verification checks on immigration applications.

This service:
1. Receives a POST request with an applicationId
2. Fetches application data from the database API
3. Downloads all documents for the application
4. Runs the VerityGraph verification pipeline
5. Returns the verification results
"""

import os
import json
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from verity_check.ingest import ingest_documents
from verity_check.perception import extract_data
from verity_check.knowledge_graph import build_graph
from verity_check.consistency_check import run_checks


# Configuration
API_INTERNAL = "https://hackatum-api-254788991896.europe-west3.run.app/api/internal/"
app = FastAPI(
    title="VerityCheck API",
    description="API for running verification checks on immigration applications",
    version="1.0.0"
)


class CheckRequest(BaseModel):
    """Request model for triggering verification checks"""
    applicationId: str


class CheckResult(BaseModel):
    """Individual check result"""
    documentTitle: str
    type: str
    checkDisplayTitle: str
    status: str  # "PASS" or "FAIL"
    message: str


class CheckResponse(BaseModel):
    """Response model for verification results - matches ValidationReport from OpenAPI"""
    applicationId: str
    isComplete: bool
    overallResult: str  # "PENDING", "SUCCESS", "WARNING", "CRITICAL_ERROR"
    checkedAt: str  # ISO 8601 datetime
    checks: list[CheckResult]


@app.get("/")
async def root():
    """Health check endpoint - also checks VLM service status"""
    vlm_status = "unknown"
    vlm_url = os.getenv("VLLM_API_URL", "http://localhost:8000/v1/chat/completions")
    base_url = vlm_url.replace("/v1/chat/completions", "/v1/models")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, timeout=2.0)
            if response.status_code == 200:
                vlm_status = "ready"
            else:
                vlm_status = f"error_{response.status_code}"
    except Exception as e:
        vlm_status = "unreachable"
        
    return {
        "message": "VerityCheck API is running", 
        "status": "ok",
        "vlm_service": vlm_status
    }


@app.post("/check", response_model=CheckResponse)
async def run_verification_check(request: CheckRequest):
    """
    Trigger verification check for an application.
    
    This endpoint:
    1. Fetches application data from the database API
    2. Downloads all associated documents
    3. Runs the VerityGraph verification pipeline
    4. Returns verification results
    """
    application_id = request.applicationId
    
    print(f"🚀 Starting verification for application {application_id}")
    
    # Create temporary directory for documents
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Step 1: Fetch application data
            if application_id == "dummy-123":
                print("🧪 Running in SIMULATION MODE")
                app_data = {
                    "firstName": "Max",
                    "lastName": "Mustermann",
                    "submittedDocuments": [
                        {
                            "type": "passport",
                            "filename": "passport.jpg",
                            "local_source": "/home/holmov/BecomingMuenchner/verity_check/tests/dummy_doc.jpg"
                        }
                    ]
                }
                print(f"✅ Loaded dummy application: {app_data.get('firstName')} {app_data.get('lastName')}")
            else:
                print(f"📡 Fetching application data for ID {application_id}...")
                async with httpx.AsyncClient() as client:
                    app_response = await client.get(
                        f"{API_INTERNAL}applications/{application_id}/data"
                    )
                    
                    if app_response.status_code == 404:
                        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
                    
                    app_response.raise_for_status()
                    app_data = app_response.json()
                    
                    print(f"✅ Found application: {app_data.get('firstName')} {app_data.get('lastName')}")
                
            # Step 2 & 3: Download, ingest, and process documents asynchronously
            print(f"📥 Processing documents asynchronously...")
            documents_data = app_data.get('submittedDocuments', [])

            if not documents_data:
                raise HTTPException(
                    status_code=400, 
                    detail="No documents found for this application"
                )
            
            # Process all documents concurrently
            tasks = [process_single_document(doc, application_id, temp_dir) for doc in documents_data]
            
            # Wait for all documents to be processed
            results = await asyncio.gather(*tasks)
            
            # Flatten results and filter out None values
            extracted_data = []
            for result in results:
                if result:
                    if isinstance(result, list):
                        extracted_data.extend(result)
                    else:
                        extracted_data.append(result)
            
            if not extracted_data:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to process any documents"
                )
            
            print(f"✅ Processed {len(extracted_data)} document pages total")
            
            # Build knowledge graph
            print("🕸️  Building Knowledge Graph...")
            G = build_graph(extracted_data)
            print(f"    Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
            
            # Run consistency checks
            print("⚖️  Running Consistency Checks...")
            alerts = run_checks(G)
            
            # Transform alerts into CheckResult format
            checks = []
            for alert in alerts:
                # Extract document title from filenames
                filenames = alert.get('filenames', [])
                doc_title = filenames[0] if filenames else "Unknown Document"
                
                # Map check name to display title
                check_display_title = alert.get('check', 'Unknown Check')
                
                # Determine document type from extracted_data
                doc_type = "unknown"
                for data_item in extracted_data:
                    if data_item.get('metadata', {}).get('filename') in filenames:
                        doc_type = data_item.get('metadata', {}).get('document_type', 'unknown')
                        break
                
                checks.append(CheckResult(
                    documentTitle=doc_title,
                    type=doc_type,
                    checkDisplayTitle=check_display_title,
                    status="FAIL",
                    message=alert.get('message', '')
                ))
            
            # Determine overall result
            if not alerts:
                overall_result = "SUCCESS"
            else:
                # Check severity levels
                high_severity_count = sum(1 for a in alerts if a.get('severity') == 'HIGH')
                if high_severity_count > 0:
                    overall_result = "CRITICAL_ERROR"
                else:
                    overall_result = "WARNING"
            
            # Log results
            if alerts:
                print(f"⚠️  Found {len(alerts)} issues!")
                for alert in alerts:
                    print(f"    - [{alert['severity']}] {alert['check']}: {alert['message']}")
            else:
                print("✅ Verification Passed!")
            
            # Get current timestamp in ISO 8601 format
            checked_at = datetime.utcnow().isoformat() + "Z"
            
            # Return results
            return CheckResponse(
                applicationId=str(application_id),
                isComplete=True,
                overallResult=overall_result,
                checkedAt=checked_at,
                checks=checks
            )
                
        except httpx.HTTPError as e:
            print(f"❌ HTTP error: {e}")
            raise HTTPException(status_code=500, detail=f"Error communicating with database API: {str(e)}")
        except Exception as e:
            print(f"❌ Error during verification: {e}")
            raise HTTPException(status_code=500, detail=f"Error during verification: {str(e)}")

async def process_single_document(doc_info: dict, application_id: str, temp_dir: str) -> dict:
    """
    Download, ingest, and run perception on a single document.
    Returns extracted data or None if processing fails.
    """
    doc_type = doc_info.get('type')
    filename = doc_info.get('filename', f"{doc_type}.pdf")
    
    print(f"  📄 Processing {doc_type} ({filename})")
    
    try:
        # Download document using the internal API endpoint or use local source
        filepath = Path(temp_dir) / filename
        
        if doc_info.get('local_source'):
            print(f"    📂 Using local source: {doc_info['local_source']}")
            import shutil
            shutil.copy(doc_info['local_source'], filepath)
            print(f"    ✅ Copied {filename}")
        else:
            doc_url = f"{API_INTERNAL}documents/{application_id}/{doc_type}"
            
            async with httpx.AsyncClient() as doc_client:
                doc_response = await doc_client.get(doc_url, timeout=30.0)
                doc_response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(doc_response.content)
                
                print(f"    ✅ Downloaded {filename}")
        
        # Ingest document (convert to images)
        # Run in thread pool since ingest_documents uses ProcessPoolExecutor
        loop = asyncio.get_event_loop()
        processed_images = await loop.run_in_executor(
            None, 
            ingest_documents, 
            [str(filepath)]
        )
        
        if not processed_images:
            print(f"    ⚠️  No images extracted from {filename}")
            return None
        
        print(f"    🖼️  Ingested {len(processed_images)} image(s) from {filename}")
        
        # Extract data using VLM (run in thread pool since it's blocking)
        results = []
        for img_data in processed_images:
            print(f"    👁️  Analyzing {img_data['filename']}...")
            result = await loop.run_in_executor(
                None,
                extract_data,
                img_data["image_base64"],
                img_data["filename"]
            )
            
            category = result["category"]
            data = result["data"]
            print(f"      → Categorized as {category}")
            
            results.append({
                "data": data,
                "metadata": {
                    "filename": img_data["filename"],
                    "page": img_data["page_number"],
                    "category": category,
                    "document_type": doc_type
                }
            })
        
        return results
        
    except Exception as e:
        print(f"    ❌ Failed to process {doc_type}: {e}")
        return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
