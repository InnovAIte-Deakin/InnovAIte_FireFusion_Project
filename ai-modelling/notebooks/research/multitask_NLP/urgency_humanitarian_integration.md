# RESEARCH: Integrating Additional Classification Heads (Urgency & Humanitarian)

## 1. Introduction

The misinformation model currently is a **single-task** classifier, which is a DeBERTa encoder with one binary head (`non_misinformation` or `misinformation`). We want to extend it into a **multi-task** model that also predicts, from the *same* social-post input:


| Task             | Type       | Labels                                                        |
| ---------------- | ---------- | ------------------------------------------------------------- |
| `misinformation` | binary     | `TRUE`, `FALSE`                                               |
| `urgency`        | 3 classes  | `NOT_USEFUL`, `NOT_URGENT`, `URGENT`                          |
| `humanitarian`   | multiclass | `HMN_DMG`, `MAT_DMG`, `WARN`, `EVAC`, `HMN_MISS`. `VOLUNTEER` |


**Urgency and humanitarian are the same integration problem.** Both are just another classification head over the shared post representation. They're only different in *label count* and *loss*.

1. All tasks share one input (a textual post) -> they **share the encoder deBERTa** and are different in
  the head.
2. **Label availability differs by data source, not by example within a source:**
  - The **misinfo** dataset carries only a misinfo label.
  - The **crisis** dataset (source of urgency/humanitarian) carries **both**
  urgency and humanitarian labels on the *same* example.

Hence, urgency and humanitarian should be trained **jointly on one input data**, while misinformation is trained on its **own** examples.

## 2. Model architecture

### 2.1 Single task (current state)

`build_fresh_classifier` in `src/models/misinformation/deberta.py` wraps
`AutoModelForSequenceClassification`, which attaches **exactly one** head to the
encoder and adjusts the loss internally:

```python
# current — single task, single head
model = AutoModelForSequenceClassification.from_pretrained(
    "microsoft/deberta-v3-large", num_labels=2, id2label=..., label2id=...,
)
logits = model(**batch).logits          # one head only
loss   = model(**batch).loss            # loss computed inside HF
```

This cannot host a second task: the head count and the loss are fixed by the wrapper.

### 2.2 Multiple tasks in parallel (proposed)

We will keep **one shared encoder** that turns a post into a vector, and attach **one small head per task** on top of it. This is *hard parameter sharing*, which is the standard multi-task setup because all three tasks read the *same* input (a post). Moreover, the encoder now learns from every task's gradients, which typically helps the smaller-data tasks.

```
AutoModel (deberta-v3-large encoder)
  │  pooled representation h  (hidden_size = 1024)
  ├── heads["misinfo"]      : Linear(1024 → 2)
  ├── heads["urgency"]      : Linear(1024 → 3)     ← NEW
  └── heads["humanitarian"] : Linear(1024 → K)     ← NEW (same pattern)
```

```python
from dataclasses import dataclass
import torch
import torch.nn as nn
from transformers import AutoConfig, AutoModel

@dataclass(frozen=True)
class TaskSpec:
    name: str
    num_labels: int
    id2label: dict[int, str]

# Every task is just a (name, num_labels, id2label) triple
MISINFO = TaskSpec("misinfo", 2, {0: "TRUE", 1: "FALSE"})
URGENCY = TaskSpec("urgency", 3, {0: "NOT_USEFUL", 1: "NOT_URGENT", 2: "URGENT"})
HUMANITARIAN = TaskSpec("humanitarian", 6, {
    0: "HMN_DMG",    # human damage
    1: "MAT_DMG",    # material damage
    2: "WARN",       # warning
    3: "EVAC",       # evacuations
    4: "HMN_MISS",   # missing people
    5: "VOLUNTEER",  # volunteering
})

class MultiTaskDeberta(nn.Module):
    def __init__(self, hf_model_id: str = "microsoft/deberta-v3-large", 
        *,
        tasks: tuple[TaskSpec, ...] = (MISINFO, URGENCY, HUMANITARIAN),
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.config = AutoConfig.from_pretrained(hf_model_id)
        self.encoder = AutoModel.from_pretrained(hf_model_id)
        self.dropout = nn.Dropout(dropout)

        hidden = self.config.hidden_size
        self.heads = nn.ModuleDict(
            {t.name: nn.Linear(hidden, t.num_labels) for t in tasks}
        )
        self.tasks: dict[str, TaskSpec] = {t.name: t for t in tasks}

    def encode(self, input_ids, attention_mask, token_type_ids=None) -> torch.Tensor:
        out = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        return self.dropout(out.last_hidden_state[:, 0])

    def forward(self, input_ids, attention_mask, token_type_ids=None, *, tasks=None):
        h = self.encode(input_ids, attention_mask, token_type_ids)
        names = tasks if tasks is not None else list(self.heads.keys())
        return {name: self.heads[name](h) for name in names}
```

### 2.3 Multitask inference

At the product level, we want **all three predictions for one post in a single pass**. Because `encode()` is shared, one forward gives every head's logits for free, and we convert each head's raw logits into a human-readable prediction.

```python
@torch.no_grad()
def classify_multitask(text, *, tokenizer, model, device, max_len) -> dict:
    model.eval()
    enc = tokenizer(text, truncation=True, padding="max_length",
                    max_length=max_len, return_tensors="pt")
    enc = {k: v.to(device) for k, v in enc.items()}
    result = {}
    for name, logits in model(input_ids=enc["input_ids"],
                              attention_mask=enc["attention_mask"],
                              token_type_ids=enc.get("token_type_ids")).items():   # all heads
        probs = torch.softmax(logits, dim=-1).squeeze(0)
        i = int(torch.argmax(probs))
        id2label = model.tasks[name].id2label
        result[name] = {"label": id2label[i], "confidence": float(probs[i]),
                        "probabilities": {id2label[j]: float(probs[j]) for j in range(len(probs))}}
    return result   # {"misinfo": {...}, "urgency": {...}, "humanitarian": {...}}
```

### 2.4 Checkpoint contract

A custom `nn.Module` can't be reloaded by HF's `from_pretrained`, and its `state_dict` is just raw tensors. Therefore, we save two things, the weights and a small manifest that allow us to rebuild the exact head structure before loading the weights into it.

```python
# save
model.encoder.config.save_pretrained(out_dir); tokenizer.save_pretrained(out_dir)
torch.save(model.state_dict(), out_dir / "model.pt")
(out_dir / "tasks.json").write_text(json.dumps({
    "hf_model_id": hf_model_id, "max_len": max_len,
    "tasks": [{"name": t.name, "num_labels": t.num_labels, "id2label": t.id2label}
              for t in model.tasks.values()]}))

# load
def load_multitask_from_checkpoint(ckpt):
    spec = json.loads((ckpt / "tasks.json").read_text())
    tokenizer = AutoTokenizer.from_pretrained(ckpt)
    tasks = tuple(TaskSpec(t["name"], t["num_labels"],
                           {int(k): v for k, v in t["id2label"].items()}) for t in spec["tasks"])
    model = MultiTaskDeberta(spec["hf_model_id"], tasks=tasks)
    model.load_state_dict(torch.load(ckpt / "model.pt", map_location="cpu"))
    return tokenizer, model, spec["max_len"]
```

## 3. Training & evaluation script

### 3.1 Single task (current)

The current model training and evaluation strategy in `src/training/deberta_train.py` only contains 1 dataloader, 1 loss (cross-entropy), and evaluates one head.

```python
# TRAIN — single task
for batch in train_loader:
    batch = {k: v.to(device) for k, v in batch.items()}
    loss  = model(**batch).loss           # CE, computed inside HF
    loss.backward(); optim.step(); optim.zero_grad()

# EVAL — single head (accuracy + macro-F1)
def evaluate_head(model, loader, device, task):
    ys, preds = [], []
    for batch in loader:
        labels = batch.pop(f"{task}_labels").tolist() if f"{task}_labels" in batch else batch["labels"].tolist()
        batch = {k: v.to(device) for k, v in batch.items()}
        logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"],
                       token_type_ids=batch.get("token_type_ids"), tasks=[task])[task]
        preds.extend(torch.argmax(logits, dim=-1).tolist()); ys.extend(labels)
    return {"accuracy": accuracy_score(ys, preds),
            "macro_f1": precision_recall_fscore_support(ys, preds, average="macro", zero_division=0)[2]}
```

The single-task loop is trivial because HF hides everything, one loader and `model(**batch).loss` computes cross-entropy internally. When own multiple heads we will have to define the loss ourselves.

### 3.2 Multiple tasks — losses

The loss contains 2 properties, including

- **per-task loss**: `misinfo` is roughly balanced -> cross-entropy. `urgency` and
`humanitarian` are imbalanced → focal-loss
- **a batch contributes the loss of the head(s) it has labels for**: a misinfo batch -> `L_misinfo`. A crisis batch → `L_urgency + L_humanitarian`.

```python
import torch.nn.functional as F

class FocalLoss(nn.Module):
    """gamma>0 down-weights easy examples; `weight` adds per-class balancing."""
    def __init__(self, gamma: float = 2.0, weight: torch.Tensor | None = None):
        super().__init__(); self.gamma = gamma; self.weight = weight
    def forward(self, logits, target):
        logp = F.log_softmax(logits, dim=-1)
        ce = F.nll_loss(logp, target, weight=self.weight, reduction="none")
        pt = logp.gather(1, target.unsqueeze(1)).squeeze(1).exp()
        return ((1.0 - pt) ** self.gamma * ce).mean()

# Per-head loss registry (class_weight tensors computed from train counts).
LOSSES = {
    "misinfo":      nn.CrossEntropyLoss(),
    "urgency":      FocalLoss(gamma=2.0, weight=urgency_class_weight),
    "humanitarian": FocalLoss(gamma=2.0, weight=humanitarian_class_weight),
}

def batch_loss(model, batch, tasks_present: list[str]) -> torch.Tensor:
    """Sum the loss over the heads this batch carries labels for (encode once)."""
    logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"],
                   token_type_ids=batch.get("token_type_ids"), tasks=tasks_present)
    return sum(LOSSES[t](logits[t], batch[f"{t}_labels"]) for t in tasks_present)
```
