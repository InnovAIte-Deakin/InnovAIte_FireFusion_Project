# Misinformation model-ready datasets

| Trainer argument | File | Records | Required fields |
| --- | --- | ---: | --- |
| Single-task --train | [PHEME training](single-task/pheme_deberta_train.json) | 1,466 | claim, label |
| Single-task --val | [PHEME validation](single-task/pheme_deberta_val.json) | 202 | claim, label |
| Multitask --misinfo | [PHEME misinformation](multitask/pheme_misinfo.json) | 1,466 | claim, label |
| Multitask --crisis | [Combined crisis data](multitask/crisis.json) | 11,416 | text, urgency, humanitarian |

## Single-task DeBERTa

The PHEME files use 0 for a true claim (non-misinformation) and 1 for a false claim (misinformation). Training covers eight breaking-news events. The 202 validation posts cover 15 rumour topics from the Germanwings crash, an event held out in full. Evaluation on Australian bushfire claims requires separate factual verdicts. Use both arguments to preserve the event split. Passing the validation file to the separate binary evaluator is appropriate for validation checks. An independent test requires a separate holdout.

From the ai-modelling directory:

```powershell
python src/training/deberta_train.py --train 'src/data/misinformation/single-task/pheme_deberta_train.json' --val 'src/data/misinformation/single-task/pheme_deberta_val.json' --output-dir 'checkpoints/pheme-single-task'
```

## Multitask DeBERTa

The default multitask misinformation head uses 0 for false and 1 for true. Its PHEME file contains the same claims as the single-task training file with reversed IDs. The Germanwings event stays outside the multitask input. The trainer creates its own row-level validation for both inputs. With the default seed, all 147 validation posts for the misinformation head cover rumour topics also represented in training.

The crisis input contains 11,416 text records. The first 5,461 are unique English CrisisTS posts. The remaining 5,955 are wildfire posts from the HumAID and CrisisMMD corpus. The humanitarian field uses eight categories. See the [model label definitions](../../models/misinformation/labels.py).

Every urgency label follows the same rule. The not-humanitarian category maps to 0 (not useful), rescue/volunteering/donations maps to 1 (not urgent), and the other six categories map to 2 (urgent). Across the full file the counts are 1,419, 3,292 and 6,705 respectively. Use independently assessed urgency labels to evaluate whether a model recognises urgent posts.

From the ai-modelling directory:

```powershell
python src/training/deberta_multitask_train.py --misinfo 'src/data/misinformation/multitask/pheme_misinfo.json' --crisis 'src/data/misinformation/multitask/crisis.json' --output-dir 'checkpoints/pheme-crisists-multitask'
```

The JSON files were read back and checked against the trainer fields and label IDs. The single-task files passed the repository loader. Both multitask inputs passed the trainer's default stratified split. These checks do not include model training.

## Inference

Send one JSON object per request to `POST /predict/misinformation`. Each record has an `id` and `content`.

- [Observed posts](inference/observed_posts.jsonl) contains 68,458 distinct post IDs from TREC-IS, the wildfire corpus and the NSW and Colorado CrisisLexT26 collections. Of these posts, 6,941 share normalized text with the crisis training input.
- [Synthetic demo posts](inference/synthetic_demo_posts.jsonl) contains 2,000 simulated requests for API testing.

Both files are unlabelled for veracity. Use them for prediction and manual review. Measuring accuracy or F1 requires independent factual verdicts.
