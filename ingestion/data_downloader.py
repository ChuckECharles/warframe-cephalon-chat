import requests
import json
import os
import lzma

def decompress_index(index_path):
    """Read the index file and return the list of manifest paths."""
    with open(index_path, 'r') as f:
        lines = f.read().strip().split('\n')
    return lines

def get_manifest_url(manifest_path):
    """Construct the full URL for a manifest from the content server."""
    base_url = "http://content.warframe.com/PublicExport/Manifest/"
    return base_url + manifest_path

def download_manifest_json(manifest_path, save_path=None):
    """Download and parse the JSON data for a given manifest path.
    
    Args:
        manifest_path (str): The manifest path from the index, e.g., 'ExportWeapons_en.json!hash'
        save_path (str, optional): If provided, save the JSON to this file path.
    
    Returns:
        dict: The parsed JSON data.
    """
    url = get_manifest_url(manifest_path)
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    if save_path:
        with open(save_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return data

def get_all_manifests(index_path='data_raw/index_en.txt'):
    """Get all available manifest paths from the decompressed index."""
    return decompress_index(index_path)


def decompress_lzma(data):
    results = []
    while True:
        decomp = lzma.LZMADecompressor(lzma.FORMAT_AUTO, None, None)
        try:
            res = decomp.decompress(data)
        except lzma.LZMAError:
            if results:
                break
            else:
                raise

        results.append(res)
        data = decomp.unused_data

        if not data:
            break
        if not decomp.eof:
            raise lzma.LZMAError(
                "Compressed data ended before the end-of-stream marker"
            )

    return b"".join(results)


def download_and_decompress(lang_code: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"index_{lang_code}.txt")
    url = f"https://origin.warframe.com/PublicExport/index_{lang_code}.txt.lzma"
    response = requests.get(url)
    byt = response.content

    length = len(byt)
    while True:
        try:
            decompressed_bytes = decompress_lzma(byt[:length])
            break
        except lzma.LZMAError:
            length -= 1

    text = decompressed_bytes.decode("utf-8")

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)

    print(f"Saved decompressed file to: {output_path}")


if __name__ == "__main__":
    # Download and decompress the index if needed
    download_and_decompress("en", "data_raw")
    
    # Get all manifests
    manifests = get_all_manifests()
    print(f"Found {len(manifests)} manifests")
    
    # Download and save each manifest as JSON
    for manifest in manifests:
        # Derive filename by removing the hash part (e.g., 'ExportWeapons_en.json!hash' -> 'ExportWeapons_en.json')
        filename = manifest.split('!')[0]
        save_path = os.path.join('data_raw', filename)
        
        print(f"Downloading and saving {manifest} to {save_path}")
        try:
            data = download_manifest_json(manifest, save_path)
            print(f"Successfully saved {filename}")
        except Exception as e:
            print(f"Failed to download {manifest}: {e}")
    
    # Example: Load and inspect a specific manifest (e.g., weapons)
    weapon_file = 'data_raw/ExportWeapons_en.json'
    if os.path.exists(weapon_file):
        with open(weapon_file, 'r') as f:
            weapon_data = json.load(f)
        
        # Find a specific item
        for entry in weapon_data.get("ExportWeapons", []):
            if entry["name"] == "Lex Prime":
                print("Found Lex Prime:")
                print(json.dumps(entry, indent=4))
                break