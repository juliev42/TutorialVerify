from tqdm.notebook import tqdm
import torch
from pinecone_text.sparse import SpladeEncoder

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"running on {device}")

splade = SpladeEncoder(device=device)

def get_sparse_vector(text, splade=splade):
    return splade.encode_documents(text)