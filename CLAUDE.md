# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository structure

This repository holds multiple independent local automations, each self-contained in its own `Automation_NN_<slug>/` folder (e.g. `Automation_01_rss_geo_news/`). There is no shared code between automations and no root-level package — each automation has its own virtual environment, `requirements.txt`, tests, README, and `CLAUDE.md`.

When adding a new automation, create a new `Automation_NN_<slug>/` folder following the same shape as `Automation_01_rss_geo_news/` rather than adding shared infrastructure speculatively — pull out shared code only once a second automation actually duplicates it.

## Working in an automation

Always `cd` into the specific `Automation_NN_<slug>/` folder before running any command — each automation's virtual environment, config, and `CLAUDE.md` live there, not at the repo root.
