#!/usr/bin/env python3
"""
Script to extract important links from tree_title.json
Creates links at each level of the parameter hierarchy:
- mode
- mode + marke
- mode + marke + year
- mode + marke + year + model
- mode + marke + year + model + mkb
"""

import json
from typing import List, Dict, Any
from urllib.parse import urlencode

# Base URL for the links
BASE_URL = "https://kiagds.ru/"

def build_url(params: Dict[str, str]) -> str:
    """Build URL with given parameters"""
    if not params:
        return BASE_URL
    return f"{BASE_URL}?{urlencode(params)}"

def extract_links(data: Dict[str, Any], current_params: Dict[str, str] = None) -> List[str]:
    """
    Recursively extract all important links from the tree structure
    
    Args:
        data: The tree data structure
        current_params: Current accumulated parameters
        
    Returns:
        List of URLs
    """
    if current_params is None:
        current_params = {}
    
    links = []
    
    # Handle mode level (top level)
    if "mode" in data and isinstance(data["mode"], list):
        for mode_item in data["mode"]:
            if mode_item.get("value"):
                mode_params = {**current_params, "mode": mode_item["value"]}
                links.append(build_url(mode_params))
                
                # Process children (marke)
                if "children" in mode_item and "marke" in mode_item["children"]:
                    marke_data = mode_item["children"]["marke"]
                    links.extend(extract_marke_level(marke_data, mode_params))
    
    return links

def extract_marke_level(marke_data: Dict[str, Any], current_params: Dict[str, str]) -> List[str]:
    """Extract links at marke level"""
    links = []
    
    if "options" in marke_data:
        for option in marke_data["options"]:
            # Skip placeholder entries (where value is null)
            if option.get("value") is None or option.get("placeholder"):
                continue
                
            marke_params = {**current_params, "marke": option["value"]}
            links.append(build_url(marke_params))
            
            # Process children (year)
            if "children" in option and "year" in option["children"]:
                year_data = option["children"]["year"]
                links.extend(extract_year_level(year_data, marke_params))
    
    return links

def extract_year_level(year_data: Dict[str, Any], current_params: Dict[str, str]) -> List[str]:
    """Extract links at year level"""
    links = []
    
    if "options" in year_data:
        for option in year_data["options"]:
            # Skip placeholder entries
            if option.get("value") is None or option.get("placeholder"):
                continue
                
            year_params = {**current_params, "year": option["value"]}
            links.append(build_url(year_params))
            
            # Process children (model)
            if "children" in option and "model" in option["children"]:
                model_data = option["children"]["model"]
                links.extend(extract_model_level(model_data, year_params))
    
    return links

def extract_model_level(model_data: Dict[str, Any], current_params: Dict[str, str]) -> List[str]:
    """Extract links at model level"""
    links = []
    
    if "options" in model_data:
        for option in model_data["options"]:
            # Skip placeholder entries
            if option.get("value") is None or option.get("placeholder"):
                continue
                
            model_params = {**current_params, "model": option["value"]}
            links.append(build_url(model_params))
            
            # Process children (mkb)
            if "children" in option and "mkb" in option["children"]:
                mkb_data = option["children"]["mkb"]
                links.extend(extract_mkb_level(mkb_data, model_params))
    
    return links

def extract_mkb_level(mkb_data: Dict[str, Any], current_params: Dict[str, str]) -> List[str]:
    """Extract links at mkb level"""
    links = []
    
    if "options" in mkb_data:
        for option in mkb_data["options"]:
            # Skip placeholder entries
            if option.get("value") is None or option.get("placeholder"):
                continue
                
            mkb_params = {**current_params, "mkb": option["value"]}
            links.append(build_url(mkb_params))
    
    return links

def main():
    """Main function to extract and save links"""
    print("Reading tree_title.json...")
    
    # Read the tree structure
    with open("tree_title.json", "r", encoding="utf-8") as f:
        tree_data = json.load(f)
    
    print("Extracting links...")
    
    # Extract all important links
    all_links = extract_links(tree_data)
    
    # Remove duplicates while preserving order
    unique_links = list(dict.fromkeys(all_links))
    
    print(f"Found {len(unique_links)} unique important links")
    
    # Save to file
    output_file = "important_links.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(unique_links, f, indent=2, ensure_ascii=False)
    
    print(f"Links saved to {output_file}")
    
    # Also save as text file for easy viewing
    output_text_file = "important_links.txt"
    with open(output_text_file, "w", encoding="utf-8") as f:
        for link in unique_links:
            f.write(link + "\n")
    
    print(f"Links also saved to {output_text_file}")
    
    # Print some statistics
    print("\n=== Statistics ===")
    
    # Count links by level
    level_counts = {
        "mode only": 0,
        "mode + marke": 0,
        "mode + marke + year": 0,
        "mode + marke + year + model": 0,
        "mode + marke + year + model + mkb": 0
    }
    
    for link in unique_links:
        param_count = link.count("&") + (1 if "?" in link else 0)
        if param_count == 1:
            level_counts["mode only"] += 1
        elif param_count == 2:
            level_counts["mode + marke"] += 1
        elif param_count == 3:
            level_counts["mode + marke + year"] += 1
        elif param_count == 4:
            level_counts["mode + marke + year + model"] += 1
        elif param_count == 5:
            level_counts["mode + marke + year + model + mkb"] += 1
    
    for level, count in level_counts.items():
        print(f"  {level}: {count} links")
    
    # Print first 10 examples
    print("\n=== First 10 links ===")
    for i, link in enumerate(unique_links[:10], 1):
        print(f"{i}. {link}")

if __name__ == "__main__":
    main()


