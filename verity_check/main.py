import os
import json
import argparse
from typing import List
from pathlib import Path
import torch
from verity_check.ingest import ingest_documents
from verity_check.perception import extract_data
from verity_check.knowledge_graph import build_graph
from verity_check.consistency_check import run_checks
import networkx as nx
from verity_check.knowledge_graph import visualize_graph


def run_pipeline(input_dir: str, output_file: str = "verification_report.json"):
    print(f"🚀 Starting VerityGraph Pipeline on {input_dir}...")
    
    # 1. Ingest
    files = [str(p) for p in Path(input_dir).glob("*") if p.is_file()]
    print(f"📂 Found {len(files)} files.")
    
    processed_images = ingest_documents(files)
    print(f"🖼️  Processed {len(processed_images)} images.")
    
    # 2. Perception
    extracted_data = []
    for img_data in processed_images:
        print(f"👁️  Analyzing {img_data['filename']}...")
        
        # Pass None for category to trigger auto-categorization
        # img_data["image_base64"] is now a list of strings
        result = extract_data(img_data["image_base64"], img_data["filename"])
        
        category = result["category"]
        data = result["data"]
        print(data)
        print(f"    -> Categorized as {category}\n\n")
        
        extracted_data.append({
            "data": data,
            "metadata": {
                "filename": img_data["filename"],
                "page": img_data["page_number"],
                "category": category
            }
        })
    # save extracted data to json
    with open("extracted_data.json", "w") as f:
        json.dump(extracted_data, f, indent=2)
    # Clear GPU cache after processing all documents
    print("🧹 Clearing cache...")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        print("✅ GPU cache cleared")

    with open("extracted_data.json", "r") as f:
        extracted_data = json.load(f)

    # 3. Build Graph
    print("🕸️  Building Knowledge Graph...")
    G = build_graph(extracted_data)
    print(f"    Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    
    # Visualize graph
    visualize_graph(G, "knowledge_graph.html")
    
    # 4. Consistency Checks
    print("⚖️  Running Consistency Checks...")
    alerts = run_checks(G)
    
    # 5. Report
    report = {
        "extracted_data": extracted_data,
        "graph_stats": {
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges()
        },
        "alerts": alerts,
        "status": "FAIL" if alerts else "PASS"
    }
    
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2, default=str)
        
    print(f"🏁 Done! Report saved to {output_file}")
    if alerts:
        print(f"⚠️  Found {len(alerts)} issues!")
        for a in alerts:
            filenames_str = ", ".join(a.get('filenames', [])) if a.get('filenames') else "N/A"
            print(f"    - [{a['severity']}] {a['check']}: {a['message']}")
            print(f"      Files: {filenames_str}")
    else:
        print("✅ Verification Passed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", help="Directory containing input documents")
    args = parser.parse_args()
    
    run_pipeline(args.input_dir)
