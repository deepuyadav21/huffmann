from flask import Flask, request, jsonify, render_template
import heapq
from collections import Counter, defaultdict

app = Flask(__name__)

# Huffman Node
class Node:
    def __init__(self, char, freq):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq


# Build Huffman Tree
def build_huffman_tree(text):
    frequency = Counter(text)
    heap = [Node(char, freq) for char, freq in frequency.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(None, left.freq + right.freq)
        merged.left = left
        merged.right = right
        heapq.heappush(heap, merged)

    return heap[0], frequency


# Generate Huffman Codes
def generate_codes(node, prefix="", codes=None):
    if codes is None:
        codes = {}
    if node.char is not None:
        codes[node.char] = prefix
    else:
        if node.left:
            generate_codes(node.left, prefix + "0", codes)
        if node.right:
            generate_codes(node.right, prefix + "1", codes)
    return codes


# Compress Text
def compress_text(text):
    root, frequency_table = build_huffman_tree(text)
    huffman_codes = generate_codes(root)
    compressed_text = "".join(huffman_codes[char] for char in text)
    return compressed_text, root, frequency_table


# Decompress Text
def decompress_text(compressed_text, root):
    result = []
    current = root
    for bit in compressed_text:
        current = current.left if bit == "0" else current.right
        if current.char:
            result.append(current.char)
            current = root
    return "".join(result)


# Utility to represent the Huffman tree
def huffman_tree_to_string(node, prefix=""):
    if node.char is not None:
        return f"{prefix} -> '{node.char}'\n"
    result = ""
    if node.left:
        result += huffman_tree_to_string(node.left, prefix + "0")
    if node.right:
        result += huffman_tree_to_string(node.right, prefix + "1")
    return result


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/compress", methods=["POST"])
def compress():
    data = request.get_json()
    text = data.get("text")
    if not text:
        return {"error": "No text provided!"}, 400

    compressed_text, huffman_tree, frequency_table = compress_text(text)
    compression_ratio = len(compressed_text) / (len(text) * 8) * 100  # % of original size
    tree_representation = huffman_tree_to_string(huffman_tree)

    return jsonify({
        "compressed_text": compressed_text,
        "frequency_table": frequency_table,
        "compression_ratio": round(compression_ratio, 2),
        "tree_representation": tree_representation,
    })


@app.route("/decompress", methods=["POST"])
def decompress():
    data = request.get_json()
    compressed_text = data.get("compressed_text")
    tree_representation = data.get("tree_representation")

    if not compressed_text or not tree_representation:
        return {"error": "Invalid input for decompression!"}, 400

    # Recreate the Huffman Tree from its representation
    def recreate_tree(lines):
        root = {}
        for line in lines.strip().split("\n"):
            path, char = line.split(" -> ")
            current = root
            for bit in path:
                if bit not in current:
                    current[bit] = {}
                current = current[bit]
            current["char"] = char.strip("'")
        return root

    def traverse_tree(tree, binary_code):
        node = tree
        for bit in binary_code:
            node = node[bit]
            if "char" in node:
                yield node["char"]
                node = tree

    huffman_tree = recreate_tree(tree_representation)
    original_text = "".join(traverse_tree(huffman_tree, compressed_text))

    return jsonify({"decompressed_text": original_text})



if __name__ == "__main__":
    app.run(debug=True)
