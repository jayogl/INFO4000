import os
from huggingface_hub import HfApi

hf_token = os.getenv("HF_TOKEN") 
api = HfApi(token=hf_token)
if os.getenv("HF_TOKEN"):
    print("Successfully Loaded Token")
else:
    print("Error: Token not Found")