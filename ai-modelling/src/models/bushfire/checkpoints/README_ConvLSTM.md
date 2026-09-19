# Current Model: Matched M1 Baseline (2019 data)

**Checkpoint:** `convlstm_forecaster.pth`
**Scaler:** `convlstm_scaler.pkl`

best-performing baseline ConvLSTM model with no BiLSTM, BiConvLSTM, or attention layers activated. Trained/validated on 2019–2020 data and evaluated on 2021 data.

## Data
- Training: 2019
- Validation: January–March 2020
- Evaluation: December 10, 2021 12:00 – December 31, 2021 12:00 UTC
- Training labels: not reported in this run's log

## Architecture
- `attention = "none"`, `use_bilstm = False`, `use_biconvlstm = False` (M1 baseline)
- `hidden_size_1 = 32`, `hidden_size_2 = 16`, `dropout = 0.2`
- Total params: 73,937

## Training config
- Loss: Tversky, `alpha = 0.3`, `beta = 0.7`
- Optimizer: Adam, `lr = 0.001`
- `batch_size = 8`, `epochs = 50` (max), `patience = 10`
- `input_steps = 30`

## Outcome
- Early stopped at epoch 40; best val loss **0.670757** at epoch 30
- Selected threshold: **0.8776**

```
Epoch    Train Loss      Val Loss        Status         
------------------------------------------------------------
1        0.990711        0.976357        BEST           
2        0.962867        0.954551        BEST           
3        0.897042        0.905712        BEST           
4        0.786936        0.827794        BEST           
5        0.626491        0.788077        BEST           
6        0.580168        0.772205        BEST           
7        0.542019        0.773424        Wait 1/10      
8        0.536885        0.742998        BEST           
9        0.542355        0.788778        Wait 1/10      
10       0.547935        0.735028        BEST           
11       0.526077        0.718620        BEST           
12       0.497252        0.712579        BEST           
13       0.504832        0.722848        Wait 1/10      
14       0.505490        0.720886        Wait 2/10      
15       0.513089        0.711054        BEST           
16       0.507271        0.713826        Wait 1/10      
17       0.494707        0.712511        Wait 2/10      
18       0.481306        0.698277        BEST           
19       0.490227        0.704705        Wait 1/10      
20       0.509298        0.686047        BEST           
21       0.479014        0.690849        Wait 1/10      
22       0.479001        0.693687        Wait 2/10      
23       0.481346        0.690323        Wait 3/10      
24       0.487950        0.681383        BEST           
25       0.467464        0.699315        Wait 1/10      
26       0.475531        0.702452        Wait 2/10      
27       0.480250        0.693908        Wait 3/10      
28       0.473943        0.702699        Wait 4/10      
29       0.460927        0.676871        BEST           
30       0.474867        0.670757        BEST           
31       0.463646        0.671679        Wait 1/10      
32       0.446259        0.675929        Wait 2/10      
33       0.453942        0.681601        Wait 3/10      
34       0.447482        0.684160        Wait 4/10      
35       0.453706        0.687665        Wait 5/10      
36       0.464834        0.699304        Wait 6/10      
37       0.431259        0.678464        Wait 7/10      
38       0.449196        0.693878        Wait 8/10      
39       0.470736        0.676095        Wait 9/10      
40       0.433618        0.674246        Wait 10/10
```

| Metric | Value |
| --- | --- |
| PR-AUC | 0.1016 |
| Skill (vs no-skill PR-AUC 0.0001) | 1038.4x |
| Precision | 0.2581 |
| Recall | 0.1333 |
| F2 | 0.1476 |
| F1 | 0.1758 |
| IoU | 0.0964 |
| Brier | 0.0001 |
| ROC-AUC | 0.5995 (inflated by class imbalance) |
| TP / FP / FN / TN | 8 / 23 / 52 / 612,968 |
| Test positive rate | 0.0098% (60 of 613,051 cells) |
