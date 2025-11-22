import networkx as nx
from typing import List, Dict, Any
from datetime import datetime
import uuid

def parse_date(date_str: str) -> datetime:
    """Parses date string YYYY-MM-DD to datetime object."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None

def parse_amount(amount_str: Any) -> float:
    """Parses currency string to float."""
    if isinstance(amount_str, (int, float)):
        return float(amount_str)
    if isinstance(amount_str, str):
        # Remove currency symbols and convert comma to dot if needed
        clean_str = amount_str.replace("€", "").replace("EUR", "").strip()
        clean_str = clean_str.replace(".", "").replace(",", ".") # German format 1.000,00 -> 1000.00
        try:
            return float(clean_str)
        except ValueError:
            return 0.0
    return 0.0

def build_graph(extracted_data_list: List[Dict[str, Any]]) -> nx.DiGraph:
    """
    Constructs a Knowledge Graph from a list of extracted document data.
    Generic implementation that creates nodes for ALL extracted fields.
    
    Args:
        extracted_data_list: List of dicts, each containing 'data' (JSON from VLM) 
                             and 'metadata' (filename, category).
                             
    Returns:
        networkx.DiGraph representing the knowledge graph.
    """
    G = nx.DiGraph()
    
    # Central Root Node
    root_id = "Root:Applicant"
    G.add_node(root_id, type="Applicant", label="Applicant")
    
    for item in extracted_data_list:
        doc_data = item.get("data", {})
        metadata = item.get("metadata", {})
        category = metadata.get("category")
        filename = metadata.get("filename")
        
        # Document Node
        doc_id = f"Document:{filename}"
        G.add_node(doc_id, type="Document", category=category, filename=filename)
        G.add_edge(root_id, doc_id, relation="has_document")
        
        # Generic field processing - create nodes for ALL fields
        for field_name, field_value in doc_data.items():
            # Skip null/None values
            if field_value is None:
                continue
            
            # Determine field type and create appropriate node
            if isinstance(field_value, bool):
                # Boolean fields
                node_id = f"Field:{field_name}:{field_value}"
                G.add_node(node_id, type="BooleanField", field=field_name, value=field_value)
                G.add_edge(doc_id, node_id, relation=f"has_{field_name}")
                
            elif isinstance(field_value, (int, float)):
                # Numeric fields (amounts, scores, etc.)
                node_id = f"Field:{field_name}:{field_value}"
                G.add_node(node_id, type="NumericField", field=field_name, value=field_value)
                G.add_edge(doc_id, node_id, relation=f"has_{field_name}")
                
            elif isinstance(field_value, str):
                # String fields - categorize by common patterns
                
                # Date fields (YYYY-MM-DD or DD.MM.YYYY)
                if any(date_keyword in field_name.lower() for date_keyword in ['date', 'from', 'until', 'start', 'end']):
                    parsed_date = parse_date(field_value)
                    if parsed_date:
                        node_id = f"Date:{field_name}:{field_value}"
                        G.add_node(node_id, type="DateField", field=field_name, value=field_value, parsed=parsed_date)
                        G.add_edge(doc_id, node_id, relation=f"has_{field_name}")
                        continue
                
                # Name fields
                if 'name' in field_name.lower():
                    node_id = f"Name:{field_value}"
                    # Check if this name node already exists (to link same person across docs)
                    if node_id not in G:
                        G.add_node(node_id, type="NameField", field=field_name, value=field_value)
                    G.add_edge(doc_id, node_id, relation=f"has_{field_name}")
                    # Also link to root if it's a person name
                    if field_name in ['surname', 'given_names', 'examinee_name', 'employee_name']:
                        G.add_edge(root_id, node_id, relation="identified_as")
                    continue
                
                # Authority/Institution fields
                if any(keyword in field_name.lower() for keyword in ['authority', 'institute', 'provider', 'landlord']):
                    node_id = f"Entity:{field_value}"
                    if node_id not in G:
                        G.add_node(node_id, type="EntityField", field=field_name, value=field_value)
                    G.add_edge(doc_id, node_id, relation=f"issued_by" if 'authority' in field_name.lower() else f"has_{field_name}")
                    continue
                
                # Generic string field
                node_id = f"Field:{field_name}:{field_value}"
                G.add_node(node_id, type="StringField", field=field_name, value=field_value)
                G.add_edge(doc_id, node_id, relation=f"has_{field_name}")
        
        # Special handling for date ranges (valid_from + valid_until)
        if 'valid_from' in doc_data and 'valid_until' in doc_data:
            valid_from = parse_date(doc_data.get('valid_from'))
            valid_until = parse_date(doc_data.get('valid_until'))
            if valid_from and valid_until:
                period_id = f"Period:{valid_from.date()}_{valid_until.date()}"
                if period_id not in G:
                    G.add_node(period_id, type="ValidityPeriod", start=valid_from, end=valid_until)
                G.add_edge(doc_id, period_id, relation="has_validity_period")
        
        # Special handling for funding periods
        if 'funding_period_start' in doc_data and 'funding_period_end' in doc_data:
            start = parse_date(doc_data.get('funding_period_start'))
            end = parse_date(doc_data.get('funding_period_end'))
            if start and end:
                period_id = f"FundingPeriod:{start.date()}_{end.date()}"
                if period_id not in G:
                    G.add_node(period_id, type="FundingPeriod", start=start, end=end)
                G.add_edge(doc_id, period_id, relation="has_funding_period")

    return G


def visualize_graph(G: nx.DiGraph, output_file: str = "knowledge_graph.html"):
    """
    Creates an interactive HTML visualization of the knowledge graph.
    
    Args:
        G: NetworkX DiGraph to visualize
        output_file: Output HTML file path
    """
    try:
        from pyvis.network import Network
    except ImportError:
        print("⚠️ pyvis not installed. Install with: pip install pyvis")
        return
    
    # Create pyvis network
    net = Network(height="900px", width="100%", directed=True, notebook=False)
    net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=250, spring_strength=0.001)
    
    # Color mapping by node type
    color_map = {
        "Applicant": "#FF6B6B",        # Red
        "Document": "#4ECDC4",         # Teal
        "NameField": "#95E1D3",        # Light green
        "DateField": "#FFD93D",        # Yellow
        "NumericField": "#6BCB77",     # Green
        "BooleanField": "#A8E6CF",     # Mint
        "StringField": "#C7CEEA",      # Light purple
        "EntityField": "#FF8B94",      # Pink
        "ValidityPeriod": "#FFA07A",   # Light salmon
        "FundingPeriod": "#98D8C8"     # Aqua
    }
    
    # Add nodes with colors and labels
    for node in G.nodes(data=True):
        node_id = node[0]
        node_data = node[1]
        node_type = node_data.get("type", "Unknown")
        
        # Create label based on node type
        if node_type == "Document":
            label = f"{node_data.get('filename', 'Unknown')}\n({node_data.get('category', 'Unknown')})"
        elif node_type == "Applicant":
            label = "Applicant"
        elif node_type == "NameField":
            label = f"👤 {node_data.get('value', '')}"
        elif node_type == "DateField":
            label = f"📅 {node_data.get('field', '')}\n{node_data.get('value', '')}"
        elif node_type == "NumericField":
            label = f"🔢 {node_data.get('field', '')}\n{node_data.get('value', '')}"
        elif node_type == "BooleanField":
            label = f"✓ {node_data.get('field', '')}\n{node_data.get('value', '')}"
        elif node_type == "EntityField":
            label = f"🏢 {node_data.get('value', '')}"
        elif node_type == "ValidityPeriod":
            label = f"⏰ Validity\n{node_data.get('start', '')} to\n{node_data.get('end', '')}"
        elif node_type == "FundingPeriod":
            label = f"💰 Funding\n{node_data.get('start', '')} to\n{node_data.get('end', '')}"
        elif node_type == "StringField":
            value = str(node_data.get('value', ''))
            # Truncate long values
            if len(value) > 30:
                value = value[:27] + "..."
            label = f"{node_data.get('field', '')}\n{value}"
        else:
            label = str(node_id)
        
        color = color_map.get(node_type, "#CCCCCC")
        net.add_node(node_id, label=label, color=color, title=str(node_data))
    
    # Add edges
    for edge in G.edges(data=True):
        source, target, edge_data = edge
        relation = edge_data.get("relation", "")
        net.add_edge(source, target, label=relation, title=relation)
    
    # Save
    net.save_graph(output_file)
    print(f"📊 Graph visualization saved to {output_file}")

