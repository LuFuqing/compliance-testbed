"""Experiment modules for the compliance-by-design testbed.

  run_scenarios.py         scenario suite: B0/B1 and S0-S6b
  sensitivity.py           Morris elementary-effects screening
  sobol.py                 Sobol S1 (binned) + ST (Saltelli/Jansen); also writes
                           results/sobol_samples.csv
  flood_event.py           the synthetic 36-hour flood event and its SL/T 853-855 phases
  calibration.py           the process stress contrast (stressed vs nominal control)
  supplementary.py         supplementary tables from the manuscript's availability note
  estimator_validation.py  analytic validation of the first-order estimators (Table 7)
  figures.py               figures 1-4 (matplotlib)
"""
