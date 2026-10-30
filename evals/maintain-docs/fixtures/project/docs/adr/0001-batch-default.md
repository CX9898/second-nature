# ADR-0001: Initial Batch Default

Status: Superseded for configuration loading in 2.x

Date: 2025-01-15

## Context

Version 1.x used small input fixtures during integration.

## Decision

The constructor and configuration loader both default to a batch size of 8.

## Consequences

This records the 1.x decision. Current configuration loading is documented in
[the configuration reference](../configuration.md).
