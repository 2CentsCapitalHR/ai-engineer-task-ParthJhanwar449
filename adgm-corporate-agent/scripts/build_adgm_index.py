# scripts/build_adgm_index.py
from src.processor.rag import build_index_from_corpus
import os
def main():
    corpus_dir = os.path.join(os.getcwd(), "resources", "adgm")
    index_path = os.path.join(os.getcwd(), "resources", "adgm_index.faiss")
    meta_path = os.path.join(os.getcwd(), "resources", "adgm_meta.json")
    build_index_from_corpus(corpus_dir, index_path, meta_path)
    print("Index built:", index_path)
if __name__ == '__main__':
    main()