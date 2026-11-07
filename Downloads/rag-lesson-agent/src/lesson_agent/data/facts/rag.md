# Reference facts for "RAG" (grounding sheet used by the judge)
- RAG = Retrieval-Augmented Generation. Introduced in the 2020 paper "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks" (Lewis et al., Facebook AI Research).
- RAG does NOT retrain or change the model's weights. It gives the model extra text at question time, inside the prompt.
- Core steps: (1) prepare a knowledge source: split documents into chunks, turn chunks into embeddings, store them; (2) embed the user's question; (3) retrieve the most similar chunks; (4) augment: put question + chunks into the prompt; (5) generate: the LLM answers using that context.
- An embedding is a list of numbers representing the meaning of text; similar meanings give similar numbers. Search by meaning is called semantic search.
- Why it matters: lets an LLM use fresh or private information it never saw in training; reduces (does not eliminate) hallucinations; answers can cite sources; updating knowledge = updating documents, cheaper than retraining.
- Limits: if retrieval picks the wrong chunk, the answer can be wrong; if the documents are wrong or outdated, so is the answer; the model can still misread context; more context costs more time and money.
- RAG vs fine-tuning: fine-tuning changes the model's weights (good for style/behaviour); RAG adds knowledge at question time (good for facts that change).
- An LLM (Large Language Model) is a program trained on huge amounts of text to predict and write text. Its knowledge stops at its training cutoff date.
