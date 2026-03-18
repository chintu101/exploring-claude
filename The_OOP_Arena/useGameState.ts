"use client";

import { useState, useCallback, useRef } from "react";
import type {
  GameState,
  ActionResponse,
  CodeTrace,
  GamePhase,
  PlayerAction,
  HeroClass,
} from "@/types/game";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

// ─── Hook return type ─────────────────────────────────────────────────────────

export interface GameStateHook {
  gameState: GameState | null;
  activeTrace: CodeTrace | null;
  enemyTrace: CodeTrace | null;
  isLoading: boolean;
  error: string | null;
  lastActionResult: ActionResponse | null;
  startNewGame: (heroClass: HeroClass, heroName: string) => Promise<void>;
  performAction: (action: PlayerAction) => Promise<void>;
  advanceWave: () => Promise<void>;
  clearError: () => void;
  resetGame: () => void;
}

// ─── Persistence helpers ──────────────────────────────────────────────────────

const STORAGE_KEY = "codequest_game_state";

function saveToStorage(state: GameState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // localStorage may be unavailable in SSR or private mode
  }
}

function loadFromStorage(): GameState | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as GameState) : null;
  } catch {
    return null;
  }
}

function clearStorage(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {}
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useGameState(): GameStateHook {
  const [gameState, setGameState] = useState<GameState | null>(() => {
    // Hydrate from localStorage on first render
    if (typeof window !== "undefined") {
      return loadFromStorage();
    }
    return null;
  });
  const [activeTrace, setActiveTrace] = useState<CodeTrace | null>(null);
  const [enemyTrace, setEnemyTrace] = useState<CodeTrace | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastActionResult, setLastActionResult] =
    useState<ActionResponse | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  // ── Internal fetch helper with abort support ──

  const apiFetch = useCallback(
    async <T>(path: string, body: unknown): Promise<T> => {
      // Cancel any in-flight request
      abortRef.current?.abort();
      abortRef.current = new AbortController();

      const res = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail ?? `HTTP ${res.status}`);
      }
      return res.json() as Promise<T>;
    },
    []
  );

  // ── Start new game ──

  const startNewGame = useCallback(
    async (heroClass: HeroClass, heroName: string) => {
      setIsLoading(true);
      setError(null);
      setActiveTrace(null);
      setEnemyTrace(null);
      setLastActionResult(null);
      try {
        const data = await apiFetch<{ game_state: GameState; message: string }>(
          "/api/new-game",
          { hero_class: heroClass, hero_name: heroName }
        );
        setGameState(data.game_state);
        saveToStorage(data.game_state);
      } catch (err: unknown) {
        if ((err as Error).name !== "AbortError") {
          setError((err as Error).message ?? "Failed to start game");
        }
      } finally {
        setIsLoading(false);
      }
    },
    [apiFetch]
  );

  // ── Perform player action ──

  const performAction = useCallback(
    async (action: PlayerAction) => {
      if (!gameState) return;
      setIsLoading(true);
      setError(null);
      try {
        const response = await apiFetch<ActionResponse>("/api/action", {
          action,
          game_state: gameState,
        });

        setGameState(response.game_state);
        saveToStorage(response.game_state);
        setActiveTrace(response.code_trace);
        setEnemyTrace(response.enemy_code_trace ?? null);
        setLastActionResult(response);
      } catch (err: unknown) {
        if ((err as Error).name !== "AbortError") {
          setError((err as Error).message ?? "Action failed");
        }
      } finally {
        setIsLoading(false);
      }
    },
    [gameState, apiFetch]
  );

  // ── Advance to next wave ──

  const advanceWave = useCallback(async () => {
    if (!gameState) return;
    setIsLoading(true);
    setError(null);
    setActiveTrace(null);
    setEnemyTrace(null);
    try {
      const data = await apiFetch<{ game_state: GameState }>(
        "/api/next-wave",
        { game_state: gameState }
      );
      setGameState(data.game_state);
      saveToStorage(data.game_state);
    } catch (err: unknown) {
      if ((err as Error).name !== "AbortError") {
        setError((err as Error).message ?? "Failed to advance wave");
      }
    } finally {
      setIsLoading(false);
    }
  }, [gameState, apiFetch]);

  const clearError = useCallback(() => setError(null), []);

  const resetGame = useCallback(() => {
    abortRef.current?.abort();
    setGameState(null);
    setActiveTrace(null);
    setEnemyTrace(null);
    setLastActionResult(null);
    setError(null);
    clearStorage();
  }, []);

  return {
    gameState,
    activeTrace,
    enemyTrace,
    isLoading,
    error,
    lastActionResult,
    startNewGame,
    performAction,
    advanceWave,
    clearError,
    resetGame,
  };
}
