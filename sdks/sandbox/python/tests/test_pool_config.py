#
# Copyright 2025 Alibaba Group Holding Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Tests for ``PoolConfig`` and ``AsyncPoolConfig`` validation."""

from __future__ import annotations

from datetime import timedelta

import pytest

from opensandbox.config.connection import ConnectionConfig
from opensandbox.config.connection_sync import ConnectionConfigSync
from opensandbox.pool import (
    AsyncPoolConfig,
    InMemoryAsyncPoolStateStore,
    InMemoryPoolStateStore,
    PoolConfig,
    PoolCreationSpec,
)


def _sync_kwargs() -> dict[str, object]:
    return {
        "pool_name": "test",
        "max_idle": 1,
        "state_store": InMemoryPoolStateStore(),
        "connection_config": ConnectionConfigSync(),
        "creation_spec": PoolCreationSpec(image="ubuntu:22.04"),
    }


def _async_kwargs() -> dict[str, object]:
    return {
        "pool_name": "test",
        "max_idle": 1,
        "state_store": InMemoryAsyncPoolStateStore(),
        "connection_config": ConnectionConfig(),
        "creation_spec": PoolCreationSpec(image="ubuntu:22.04"),
    }


def test_default_acquire_min_remaining_ttl_is_60s() -> None:
    config = PoolConfig(**_sync_kwargs())  # type: ignore[arg-type]
    assert config.acquire_min_remaining_ttl == timedelta(seconds=60)


def test_async_default_acquire_min_remaining_ttl_is_60s() -> None:
    config = AsyncPoolConfig(**_async_kwargs())  # type: ignore[arg-type]
    assert config.acquire_min_remaining_ttl == timedelta(seconds=60)


def test_negative_acquire_min_remaining_ttl_rejected() -> None:
    with pytest.raises(ValueError, match="acquire_min_remaining_ttl must be non-negative"):
        PoolConfig(**_sync_kwargs(), acquire_min_remaining_ttl=timedelta(seconds=-1))  # type: ignore[arg-type]


def test_acquire_min_remaining_ttl_at_or_above_idle_timeout_rejected() -> None:
    # Default 60s threshold against a 30s idle_timeout ⇒ every freshly warmed entry
    # would fail the check, so build() must reject this misconfiguration upfront.
    with pytest.raises(
        ValueError, match="strictly less than"
    ):
        PoolConfig(**_sync_kwargs(), idle_timeout=timedelta(seconds=30))  # type: ignore[arg-type]


def test_async_acquire_min_remaining_ttl_at_or_above_idle_timeout_rejected() -> None:
    with pytest.raises(
        ValueError, match="strictly less than"
    ):
        AsyncPoolConfig(**_async_kwargs(), idle_timeout=timedelta(seconds=30))  # type: ignore[arg-type]


def test_acquire_min_remaining_ttl_just_below_idle_timeout_accepted() -> None:
    config = PoolConfig(
        **_sync_kwargs(),  # type: ignore[arg-type]
        idle_timeout=timedelta(seconds=10),
        acquire_min_remaining_ttl=timedelta(seconds=9),
    )
    assert config.acquire_min_remaining_ttl == timedelta(seconds=9)
    assert config.idle_timeout == timedelta(seconds=10)


def test_zero_acquire_min_remaining_ttl_opts_out() -> None:
    # Explicit Duration.ZERO ↔ legacy binary-expiry behavior; valid configuration.
    config = PoolConfig(
        **_sync_kwargs(),  # type: ignore[arg-type]
        acquire_min_remaining_ttl=timedelta(0),
    )
    assert config.acquire_min_remaining_ttl == timedelta(0)
