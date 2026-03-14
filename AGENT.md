# Agent

## Overview

This project implements a simple CLI LLM agent.

The agent receives a question from the command line, sends it to an LLM, and outputs a structured JSON response.

## Architecture

User question
↓
agent.py
↓
OpenAI-compatible API
↓
LLM response
↓
JSON output

## LLM Provider

Provider: Qwen Code API  
Model: qwen3-coder-plus

Reason:
- OpenAI-compatible
- Free usage tier
- Works without a credit card

## Environment Configuration

Credentials are stored in:

.env.agent.secret

Variables:

LLM_API_KEY  
LLM_API_BASE  
LLM_MODEL  

## Running the agent

Example:
