import os

import torch
from sentence_transformers import SentenceTransformer, util


def create_mapping_cluster(
    target_categories: list[str],
    data_entries: list[str],
    model_name: str,
    path_to_model: str,
) -> dict[str, list[str]]:

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    if os.path.exists(path_to_model):
        model = SentenceTransformer(path_to_model, device=device)
    else:
        model = SentenceTransformer(model_name, device=device)
        model.save(path_to_model)

    category_embeddings = model.encode(
        target_categories,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )
    entry_embeddings = model.encode(
        data_entries,
        convert_to_tensor=True,
        normalize_embeddings=True,
    )

    similarities = util.cos_sim(entry_embeddings, category_embeddings)
    best_matches = similarities.argmax(dim=1)

    mapping: dict[str, list[str]] = {category: [] for category in target_categories}
    for entry, match_index in zip(data_entries, best_matches):
        mapping[target_categories[match_index]].append(entry)

    return mapping
