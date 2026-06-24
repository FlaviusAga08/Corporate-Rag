import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, pipeline
from utils.vector_store import ChromaVectorStore

MODEL_ID = "qwen2.5:7b"

_QUANT_CONFIG = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4",
)

class RAGPipeline:
    def __init__(self):
        self.vector_store = ChromaVectorStore()
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=_QUANT_CONFIG,
            device_map="auto",
        )
        self.llm = pipeline("text-generation", model=model, tokenizer=tokenizer)

    def retrieve(self, query: str, k: int = 3) -> str:
        return self.vector_store.query(query, k=k)

    def generate(self, query: str, context: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "Ești un asistent AI pentru documente în limba română."
                    "Reguli:"
                    "- Răspunde întotdeauna în limba română."
                    "- Nu folosi alte limbi decât româna."
                    "- Pentru întrebări bazate pe documente, folosește doar contextul primit."
                    "- Dacă informația nu există în context, spune clar că nu ai găsit informația."
                    "- Nu inventa informații."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nÎntrebare: {query}",
            },
        ]
        output = self.llm(messages, max_new_tokens=512, do_sample=False)
        return output[0]["generated_text"][-1]["content"]

    def answer_query(self, query: str) -> str:
        context = self.retrieve(query)
        return self.generate(query, context=" ".join(context))