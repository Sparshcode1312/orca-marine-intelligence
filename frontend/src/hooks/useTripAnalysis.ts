import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  analyzeTrip as requestTripAnalysis,
  OrcaApiError,
} from "../api/orcaApi";

import type {
  IntelligenceDecision,
  TripAnalysisRequest,
} from "../types/orca";


interface UseTripAnalysisResult {
  decision: IntelligenceDecision | null;
  error: string | null;
  isLoading: boolean;
  analyze: (
    request: TripAnalysisRequest,
  ) => Promise<IntelligenceDecision | null>;
  reset: () => void;
}


export function useTripAnalysis(): UseTripAnalysisResult {
  const [decision, setDecision] =
    useState<IntelligenceDecision | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const [isLoading, setIsLoading] =
    useState(false);

  const activeRequestId = useRef(0);
  const isMounted = useRef(true);


 useEffect(() => {
  // React StrictMode re-runs effects during development.
  // Reset the mounted state whenever the effect is initialized.
  isMounted.current = true;

  return () => {
    isMounted.current = false;
    activeRequestId.current += 1;
  };
}, []);


  const analyze = useCallback(
    async (
      request: TripAnalysisRequest,
    ): Promise<IntelligenceDecision | null> => {
      const requestId = activeRequestId.current + 1;
      activeRequestId.current = requestId;

      setIsLoading(true);
      setError(null);
      setDecision(null);

      try {
        const result = await requestTripAnalysis(request);

        if (
          !isMounted.current ||
          requestId !== activeRequestId.current
        ) {
          return null;
        }

        setDecision(result);

        return result;
      } catch (requestError) {
        if (
          !isMounted.current ||
          requestId !== activeRequestId.current
        ) {
          return null;
        }

        const message =
          requestError instanceof OrcaApiError
            ? requestError.message
            : "An unexpected error occurred.";

        setError(message);

        return null;
      } finally {
        if (
          isMounted.current &&
          requestId === activeRequestId.current
        ) {
          setIsLoading(false);
        }
      }
    },
    [],
  );


  const reset = useCallback(() => {
    activeRequestId.current += 1;

    setDecision(null);
    setError(null);
    setIsLoading(false);
  }, []);


  return {
    decision,
    error,
    isLoading,
    analyze,
    reset,
  };
}