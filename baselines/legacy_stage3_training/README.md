# Legacy Stage3 Training Baseline

This directory documents the role of the historical mixed `stage3_training/` mainline.

## Current Implementation Root

The real implementation still lives in:

- `stage3_training/`

## Why It Is Kept

The historical mixed stage3 mainline still matters because it:

- trained the original MLP classifiers and regressor
- built candidate pools
- ran cascade scoring
- produced validation manifests
- provided the starting point for later plan-A and real-GA work

## Why It Is No Longer the Main Thesis Narrative

It mixes together:

- prediction
- ranking
- optimization

The new architecture separates those concerns:

- `prediction/`
- `optimization/`

## How To Use It Now

Treat `stage3_training/` as:

- a legacy candidate-discovery baseline
- a source of historical models and seed rankings
- a comparison point for the newer optimization logic
